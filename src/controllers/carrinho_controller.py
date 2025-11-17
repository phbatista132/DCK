from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.models import Carrinho, ItemCarrinho, Produtos
from src.controllers.estoque_controller import EstoqueController
from src.utils.logKit.config_logging import get_logger


class CarrinhoController:
    """Controller para gerenciar carrinhos de compras persistidos"""

    def __init__(self):
        self.carrinho_log = get_logger("LoggerCarrinhoController", "DEBUG")
        self.estoque_controller = EstoqueController()

    def _limpar_carrinhos_expirados(self, db: Session) -> int:
        """
        Marca carrinhos expirados e libera reservas

        Returns:
            Quantidade de carrinhos expirados
        """
        try:
            agora = datetime.now()

            carrinhos_expirados = db.query(Carrinho).filter(Carrinho.status == 'ATIVO',
                                                            Carrinho.expira_em < agora).all()

            count = 0
            for carrinho in carrinhos_expirados:

                for item in carrinho.itens:
                    self.estoque_controller.liberar_reserva(db=db, produto_id=item.produto_id,
                                                            usuario_id=carrinho.usuario_id)
                carrinho.status = 'EXPIRADO'
                count += 1

                self.carrinho_log.info(
                    f"Carrinho expirado: ID {carrinho.id_carrinho} - "
                    f"Usuário {carrinho.usuario_id}"
                )

            if count > 0:
                db.commit()

            return count

        except Exception:
            db.rollback()
            self.carrinho_log.exception("Erro ao limpar carrinhos expirados")
            return 0

    def obter_ou_criar_carrinho(
            self, db: Session, usuario_id: int) -> Tuple[bool, Carrinho, str]:
        """
        Obtém carrinho ativo do usuário ou cria um novo

        Args:
            db: Sessão do banco
            usuario_id: ID do usuário

        Returns:
            (novo: bool, carrinho: Carrinho, mensagem: str)
        """
        try:

            self._limpar_carrinhos_expirados(db)

            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            if carrinho:
                carrinho.renovar_expiracao()
                db.commit()
                self.carrinho_log.debug(f"Carrinho existente recuperado: ID {carrinho.id_carrinho}")
                return False, carrinho, "Carrinho recuperado"

            expira_em = datetime.now() + timedelta(minutes=30)
            carrinho = Carrinho(usuario_id=usuario_id, expira_em=expira_em, status='ATIVO')

            db.add(carrinho)
            db.commit()
            db.refresh(carrinho)

            self.carrinho_log.info(f"Novo carrinho criado: ID {carrinho.id_carrinho} para usuário {usuario_id}")
            return True, carrinho, "Novo carrinho criado"

        except Exception:
            db.rollback()
            self.carrinho_log.exception(f"Erro ao obter/criar carrinho para usuário {usuario_id}")
            raise

    def adicionar_item(self, db: Session, usuario_id: int, produto_id: int, quantidade: int) -> Tuple[bool, str]:
        """
        Adiciona item ao carrinho do usuário

        Fluxo:
        1. Obter/criar carrinho ativo
        2. Verificar se produto existe e está ativo
        3. Reservar estoque
        4. Adicionar ao carrinho (ou atualizar quantidade se já existe)
        5. Recalcular subtotal
        """
        try:
            if quantidade <= 0:
                return False, "Quantidade deve ser maior que zero"

            novo, carrinho, msg = self.obter_ou_criar_carrinho(db, usuario_id)

            produto = db.query(Produtos).filter(Produtos.codigo == produto_id, Produtos.ativo == True).first()

            if not produto:
                return False, "Produto não encontrado ou desativado"

            item_existente = db.query(ItemCarrinho).filter(ItemCarrinho.carrinho_id == carrinho.id_carrinho,
                                                           ItemCarrinho.produto_id == produto_id).first()

            if item_existente:
                nova_quantidade = item_existente.quantidade + quantidade

                disponivel, _ = self.estoque_controller.verificar_disponibilidade(db, produto_id, quantidade, usuario_id)

                if not disponivel:
                    return False, "Estoque insuficiente para adicionar esta quantidade"

                sucesso, _ = self.estoque_controller.reservar_estoque(db, produto_id, quantidade, usuario_id)

                if not sucesso:
                    return False, "Não foi possível reservar o estoque"

                item_existente.quantidade = nova_quantidade
                item_existente.calcular_subtotal()

                self.carrinho_log.info(
                    f"Quantidade atualizada no carrinho: Produto {produto_id} - "
                    f"Nova quantidade: {nova_quantidade}")
            else:

                disponivel, _ = self.estoque_controller.verificar_disponibilidade(db, produto_id, quantidade, usuario_id)

                if not disponivel:
                    return False, "Estoque insuficiente"

                sucesso, _ = self.estoque_controller.reservar_estoque(db, produto_id, quantidade, usuario_id)

                if not sucesso:
                    return False, "Não foi possível reservar o estoque"

                item = ItemCarrinho(carrinho_id=carrinho.id_carrinho, produto_id=produto_id, quantidade=quantidade,
                                    preco_unitario=produto.valor)
                item.calcular_subtotal()

                db.add(item)

                self.carrinho_log.info(
                    f"Item adicionado ao carrinho: Produto {produto_id} - "
                    f"Quantidade: {quantidade}"
                )

            carrinho.calcular_subtotal()
            carrinho.renovar_expiracao()

            db.commit()

            return True, "Item adicionado ao carrinho com sucesso"

        except Exception as e:
            db.rollback()
            self.carrinho_log.exception(f"Erro ao adicionar item ao carrinho")
            return False, f"Erro: {e}"

    def remover_item(self, db: Session, usuario_id: int, produto_id: int) -> Tuple[bool, str]:
        """Remove item do carrinho e libera reserva"""
        try:

            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            if not carrinho:
                return False, "Carrinho não encontrado"

            item = db.query(ItemCarrinho).filter(ItemCarrinho.carrinho_id == carrinho.id_carrinho,
                                                 ItemCarrinho.produto_id == produto_id).first()

            if not item:
                return False, "Item não encontrado no carrinho"

            self.estoque_controller.liberar_reserva(db=db, produto_id=produto_id, usuario_id=usuario_id)

            db.delete(item)
            carrinho.calcular_subtotal()
            carrinho.renovar_expiracao()

            db.commit()

            self.carrinho_log.info(
                f"Item removido do carrinho: Produto {produto_id} - "
                f"Carrinho {carrinho.id_carrinho}")

            return True, "Item removido do carrinho"

        except Exception as e:
            db.rollback()
            self.carrinho_log.exception("Erro ao remover item")
            return False, f"Erro: {e}"

    def alterar_quantidade(self, db: Session, usuario_id: int, produto_id: int, nova_quantidade: int
                           ) -> Tuple[bool, str]:
        """Altera quantidade de um item no carrinho"""
        try:
            if nova_quantidade <= 0:
                return False, "Quantidade deve ser maior que zero"

            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            if not carrinho:
                return False, "Carrinho não encontrado"

            item = db.query(ItemCarrinho).filter(ItemCarrinho.carrinho_id == carrinho.id_carrinho,
                                                 ItemCarrinho.produto_id == produto_id).first()

            if not item:
                return False, "Item não encontrado no carrinho"

            quantidade_atual = item.quantidade
            diferenca = nova_quantidade - quantidade_atual

            if diferenca > 0:
                sucesso, _ = self.estoque_controller.reservar_estoque(
                    db, produto_id, diferenca, usuario_id
                )
                if not sucesso:
                    return False, "Estoque insuficiente"

            elif diferenca < 0:
                self.estoque_controller.liberar_reserva(db=db, produto_id=produto_id, usuario_id=usuario_id)

                self.estoque_controller.reservar_estoque(db, produto_id, nova_quantidade, usuario_id)

            item.quantidade = nova_quantidade
            item.calcular_subtotal()

            carrinho.calcular_subtotal()
            carrinho.renovar_expiracao()

            db.commit()

            return True, "Quantidade alterada com sucesso"

        except Exception as e:
            db.rollback()
            self.carrinho_log.exception("Erro ao alterar quantidade")
            return False, f"Erro: {e}"

    def obter_carrinho(self, db: Session, usuario_id: int) -> Optional[Carrinho]:
        """Retorna carrinho ativo do usuário"""
        try:
            self._limpar_carrinhos_expirados(db)

            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            return carrinho

        except Exception:
            self.carrinho_log.exception("Erro ao obter carrinho")
            return None

    def limpar_carrinho(self, db: Session, usuario_id: int) -> Tuple[bool, str]:
        """Limpa carrinho (cancela e libera todas as reservas)"""
        try:
            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            if not carrinho:
                return True, "Carrinho já estava vazio"

            for item in carrinho.itens:
                self.estoque_controller.liberar_reserva(db=db, produto_id=item.produto_id, usuario_id=usuario_id)

            carrinho.status = 'CANCELADO'

            db.commit()

            self.carrinho_log.info(f"Carrinho limpo: ID {carrinho.id_carrinho}")

            return True, "Carrinho limpo com sucesso"

        except Exception as e:
            db.rollback()
            self.carrinho_log.exception("Erro ao limpar carrinho")
            return False, f"Erro: {e}"
