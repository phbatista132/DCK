from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from src.utils.logKit.config_logging import get_logger
from src.database import Produtos, MovimentacaoEstoque, Reserva


class EstoqueController:
    def __init__(self):
        self.estoque_log = get_logger("LoggerEstoqueController", "DEBUG")

    def _limpar_reservas_expiradas(self, db: Session) -> int:
        """
        Remove reservas expiradas do banco

        Returns:
            Quantidade de reservas limpas
        """
        try:
            agora = datetime.now()

            reservas_expiradas = db.query(Reserva).filter(Reserva.ativa == True, Reserva.expira_em < agora).all()

            count = 0
            for reserva in reservas_expiradas:

                produto = db.query(Produtos).filter(Produtos.codigo == reserva.produto_id).first()

                if produto:
                    produto.quantidade_reservada -= reserva.quantidade

                    # Garantir que não fique negativo
                    if produto.quantidade_reservada < 0:
                        produto.quantidade_reservada = 0

                # Marcar reserva como inativa
                reserva.ativa = False
                count += 1

                self.estoque_log.info(
                    f"Reserva expirada: Produto {reserva.produto_id} - "
                    f"{reserva.quantidade} unidades liberadas (User: {reserva.usuario_id})"
                )

            if count > 0:
                db.commit()
                self.estoque_log.info(f"{count} reservas expiradas limpas")

            return count

        except Exception as e:
            db.rollback()
            self.estoque_log.exception("Erro ao limpar reservas expiradas")
            return 0

    def repor_estoque(self, db: Session, id_item: int, qtd: int, usuario_id: Optional[int] = None) -> str:
        """Adiciona quantidade ao estoque"""
        try:

            if qtd <= 0:
                self.estoque_log.warning("Quantidade menor/igual a zero")
                return "Quantidade menor ou igual a zero, sem possibilidade de reposição"

            produto = db.query(Produtos).filter(Produtos.codigo == id_item, Produtos.ativo == True).first()

            if not produto:
                self.estoque_log.warning(f"Produto {id_item} não localizado ou desativado")
                return "Produto não localizado ou desativado"

            estoque_anterior = produto.quantidade_estoque
            produto.quantidade_estoque += qtd

            movimentacao = MovimentacaoEstoque(
                produto_id=id_item,
                tipo='ENTRADA',
                quantidade=qtd,
                estoque_anterior=estoque_anterior,
                estoque_posterior=produto.quantidade_estoque,
                usuario_id=usuario_id,
                observacao=f"Reposição de estoque"
            )
            db.add(movimentacao)
            db.commit()

            self.estoque_log.info(
                f"Produto {produto.nome} reposto em {qtd} unidades "
                f"({estoque_anterior} → {produto.quantidade_estoque})"
            )
            return f"Item reposto com sucesso"

        except Exception as e:
            db.rollback()
            self.estoque_log.exception("Erro ao repor estoque")
            return f'Erro interno ao repor estoque'

    def produto_habilitado(self, db: Session, id_produto: int) -> tuple[bool, str]:
        """Verifica se produto esta habilitado"""
        try:

            produto = db.query(Produtos).filter(Produtos.codigo == id_produto, Produtos.ativo == True).first()

            if not produto:
                self.estoque_log.warning(f"Produto: {id_produto} não localizado")
                return False, "Produto não localizado ou não habilitado"

            self.estoque_log.info(f"Produto: {produto.nome} Habilitado em estoque")
            return True, f'Produto: {produto.nome} Habilitado'

        except Exception as e:
            self.estoque_log.exception("Erro ao verificar produto")
            return False, f'Erro: {e}'

    def verificar_disponibilidade(self, db: Session, produto_id: int, quantidade: int, usuario: int) -> tuple[bool, int]:
        """
        Verifica disponibilidade real considerando reservas

        Returns:
            (disponível: bool, quantidade_disponivel: int)
        """
        try:
            self._limpar_reservas_expiradas(db)

            produto = db.query(Produtos).filter(Produtos.codigo == produto_id).first()

            if not produto:
                self.estoque_log.warning(f"Produto não localizado em estoque")
                return False, 0

            quantidade_disponivel = produto.quantidade_estoque - produto.quantidade_reservada
            self.estoque_log.info(f"Produto verificado: {produto.nome} Usuario:{usuario} ")
            return quantidade_disponivel >= quantidade, quantidade_disponivel

        except Exception:
            return False, 0

    def reservar_estoque(self, db: Session, produto_id: int, quantidade: int, usuario_id: int,
                         minutos_expiracao: int = 30) -> Tuple[bool, Optional[int]]:
        """
        Reserva estoque temporariamente (para carrinho)
        Reserva expira em 30 minutos
        """
        try:

            if quantidade <= 0:
                self.estoque_log.warning("Quantidade inválida para reserva")
                return False

            self._limpar_reservas_expiradas(db)

            produto = db.query(Produtos).filter(Produtos.codigo == produto_id).first()

            if not produto:
                self.estoque_log.warning(f"Produto: {produto_id} não encotrado")
                return False, None

            estoque_real = produto.quantidade_estoque
            reservado = produto.quantidade_reservada
            disponivel = estoque_real - reservado

            if disponivel < quantidade:
                self.estoque_log.warning(
                    f"Reserva negada: Produto {produto_id} - "
                    f"Solicitado: {quantidade}, Disponível: {disponivel}"
                )
                return False, None

            expira_em = datetime.now() + timedelta(minutes=minutos_expiracao)

            reserva = Reserva(
                produto_id=produto_id,
                usuario_id=usuario_id,
                quantidade=quantidade,
                expira_em=expira_em
            )
            produto.quantidade_reservada += quantidade

            db.add(reserva)
            db.commit()
            db.refresh(reserva)

            self.estoque_log.info(
                f"Reserva criada: {quantidade} unidades do produto {produto_id} "
                f"para usuário {usuario_id} (ID Reserva: {reserva.id_reserva}, "
                f"expira em {minutos_expiracao}min)"
            )

            return True, reserva.id_reserva

        except Exception as e:
            self.estoque_log.exception(f"Erro ao reservar produto {produto_id}")
            return False, None

    def liberar_reserva(self, db: Session, reserva_id: Optional[int] = None, produto_id: Optional[int] = None,
                        usuario_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Libera reserva de estoque (item removido do carrinho)

        Pode liberar por:
        - reserva_id: Libera uma reserva específica
        - produto_id + usuario_id: Libera todas as reservas daquele produto para aquele usuário

        Args:
            db: Sessão do banco
            reserva_id: ID da reserva específica
            produto_id: ID do produto
            usuario_id: ID do usuário

        Returns:
            (sucesso: bool, mensagem: str)
        """
        try:
            query = db.query(Reserva).filter(Reserva.ativa == True)

            if reserva_id:
                # Liberar reserva específica
                query = query.filter(Reserva.id_reserva == reserva_id)
            elif produto_id and usuario_id:
                # Liberar todas as reservas daquele produto para aquele usuário
                query = query.filter(
                    Reserva.produto_id == produto_id,
                    Reserva.usuario_id == usuario_id
                )
            else:
                return False, "Necessário fornecer reserva_id ou (produto_id + usuario_id)"

            reservas = query.all()

            if not reservas:
                self.estoque_log.warning("Nenhuma reserva ativa encontrada")
                return False, "Sem reservas para liberar"

            total_liberado = 0
            for reserva in reservas:
                # Liberar quantidade reservada do produto
                produto = db.query(Produtos).filter(
                    Produtos.codigo == reserva.produto_id
                ).first()

                if produto:
                    produto.quantidade_reservada -= reserva.quantidade

                    # Garantir que não fique negativo
                    if produto.quantidade_reservada < 0:
                        produto.quantidade_reservada = 0

                # Marcar reserva como inativa
                reserva.ativa = False
                total_liberado += reserva.quantidade

                self.estoque_log.info(
                    f"Reserva liberada: Produto {reserva.produto_id} - "
                    f"{reserva.quantidade} unidades (User: {reserva.usuario_id})"
                )

            db.commit()

            return True, f"{total_liberado} unidades liberadas"

        except Exception as e:
            db.rollback()
            self.estoque_log.exception("Erro ao liberar reserva")
            return False, f"Erro: {e}"

    def saida_estoque(
            self,
            db: Session,
            id_produto: int,
            quantidade: int,
            usuario_id: int,
            venda_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Realiza baixa real no estoque (venda finalizada)

        Fluxo:
        1. Diminui quantidade_estoque
        2. Diminui quantidade_reservada
        3. Desativa reservas do usuário para este produto
        4. Registra movimentação
        """
        try:
            produto = db.query(Produtos).filter(Produtos.codigo == id_produto).first()

            if not produto:
                return False, "Produto não encontrado"

            estoque_atual = produto.quantidade_estoque

            # Validar estoque suficiente
            if estoque_atual < quantidade:
                self.estoque_log.error(
                    f"ERRO CRÍTICO: Estoque insuficiente! "
                    f"Produto: {produto.nome} (ID: {id_produto}), "
                    f"Estoque: {estoque_atual}, Solicitado: {quantidade}"
                )
                return False, "Estoque insuficiente"

            # 1. Baixa no estoque real
            produto.quantidade_estoque -= quantidade

            # 2. Liberar da quantidade reservada
            if produto.quantidade_reservada >= quantidade:
                produto.quantidade_reservada -= quantidade
            else:
                # Se por algum motivo não há reserva suficiente, zerar
                produto.quantidade_reservada = 0

            # 3. Desativar reservas do usuário para este produto
            reservas_usuario = db.query(Reserva).filter(
                Reserva.produto_id == id_produto,
                Reserva.usuario_id == usuario_id,
                Reserva.ativa == True
            ).all()

            for reserva in reservas_usuario:
                reserva.ativa = False

            # 4. Registrar movimentação
            movimentacao = MovimentacaoEstoque(
                produto_id=id_produto,
                tipo='SAIDA',
                quantidade=-quantidade,
                estoque_anterior=estoque_atual,
                estoque_posterior=produto.quantidade_estoque,
                usuario_id=usuario_id,
                venda_id=venda_id,
                observacao=f"Venda finalizada (ID: {venda_id})"
            )

            db.add(movimentacao)
            db.commit()

            self.estoque_log.info(
                f"Saída de estoque: {produto.nome} (ID: {id_produto}) - "
                f"{quantidade} unidades | Estoque: {estoque_atual} → {produto.quantidade_estoque}"
            )

            return True, f"Saída realizada: {quantidade} unidades de '{produto.nome}'"

        except Exception as e:
            db.rollback()
            self.estoque_log.exception("Erro ao realizar saída de estoque")
            return False, f'Erro: {e}'

    def obter_reservas_usuario(self, db: Session, usuario_id: int) -> List[Reserva]:
        """
        Retorna todas as reservas ativas de um usuário

        Útil para:
        - Exibir carrinho
        - Verificar tempo restante
        - Limpar carrinho
        """
        try:
            # Limpar expiradas primeiro
            self._limpar_reservas_expiradas(db)

            reservas = db.query(Reserva).filter(Reserva.usuario_id == usuario_id, Reserva.ativa == True).order_by(
                Reserva.data_criacao.desc()).all()

            return reservas

        except Exception as e:
            self.estoque_log.exception(f"Erro ao buscar reservas do usuário {usuario_id}")
            return []

    def limpar_carrinho_usuario(self, db: Session, usuario_id: int) -> Tuple[bool, str]:
        """
        Limpa todas as reservas (carrinho) de um usuário

        Args:
            db: Sessão do banco
            usuario_id: ID do usuário

        Returns:
            (sucesso: bool, mensagem: str)
        """
        try:
            reservas = db.query(Reserva).filter(
                Reserva.usuario_id == usuario_id,
                Reserva.ativa == True
            ).all()

            if not reservas:
                return True, "Carrinho já estava vazio"

            total_liberado = 0
            produtos_afetados = set()

            for reserva in reservas:
                # Liberar do produto
                produto = db.query(Produtos).filter(
                    Produtos.codigo == reserva.produto_id
                ).first()

                if produto:
                    produto.quantidade_reservada -= reserva.quantidade
                    if produto.quantidade_reservada < 0:
                        produto.quantidade_reservada = 0
                    produtos_afetados.add(produto.nome)

                # Desativar reserva
                reserva.ativa = False
                total_liberado += reserva.quantidade

            db.commit()

            self.estoque_log.info(
                f"Carrinho limpo: Usuário {usuario_id} - "
                f"{total_liberado} unidades liberadas de {len(produtos_afetados)} produtos"
            )

            return True, f"Carrinho limpo: {total_liberado} unidades liberadas"

        except Exception as e:
            db.rollback()
            self.estoque_log.exception(f"Erro ao limpar carrinho do usuário {usuario_id}")
            return False, f"Erro: {e}"
