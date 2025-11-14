from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database.models import (Vendas, ItemVenda, Carrinho, Clientes, Produtos, MovimentacaoEstoque)
from src.controllers.estoque_controller import EstoqueController
from src.controllers.carrinho_controller import CarrinhoController
from src.utils.logKit.config_logging import get_logger


class VendaController:
    def __init__(self):
        self.vendas_log = get_logger("LoggerVendasController", "DEBUG")
        self.estoque_controller = EstoqueController()
        self.carrinho_controller = CarrinhoController()

    def adicionar_item_carrinho(self, db: Session, usuario_id: int, produto_id: int, quantidade: int) -> Tuple[
        bool, str]:
        """
        Adiciona item ao carrinho do usuário

        Wrapper para CarrinhoController (mantém compatibilidade com rotas antigas)
        """
        return self.carrinho_controller.adicionar_item(db=db, usuario_id=usuario_id, produto_id=produto_id,
                                                       quantidade=quantidade)

    def ver_carrinho(self, db: Session, usuario_id: int) -> Optional[Carrinho]:
        """
        Retorna carrinho atual do usuário

        Returns:
            Carrinho com itens carregados ou None
        """
        return self.carrinho_controller.obter_carrinho(db, usuario_id)

    def remover_item_carrinho(self, db: Session, usuario_id: int, produto_id: int) -> Tuple[bool, str]:
        """Remove item do carrinho"""
        return self.carrinho_controller.remover_item(db=db, usuario_id=usuario_id, produto_id=produto_id)

    def alterar_quantidade_carrinho(self, db: Session, usuario_id: int, produto_id: int, nova_quantidade: int) -> Tuple[
        bool, str]:
        """Altera quantidade de item no carrinho"""
        return self.carrinho_controller.alterar_quantidade(db=db, usuario_id=usuario_id, produto_id=produto_id,
                                                           nova_quantidade=nova_quantidade)

    def cancelar_carrinho(self, db: Session, usuario_id: int) -> Tuple[bool, str]:
        """Cancela carrinho e libera todas as reservas"""
        return self.carrinho_controller.limpar_carrinho(db, usuario_id)

    def finalizar_venda(
            self, db: Session, usuario_id: int, cpf_cliente: Optional[str] = None, forma_pagamento: str = "Debito",
            percentual_desconto: float = 0) -> Tuple[bool, str, Optional[dict]]:
        """
               Finaliza venda convertendo carrinho em venda

               Fluxo:
               1. Validar carrinho ativo e não vazio
               2. Validar cliente (se CPF fornecido)
               3. Criar Venda
               4. Converter itens do carrinho em itens de venda
               5. Aplicar desconto (se houver)
               6. Dar baixa no estoque
               7. Registrar movimentações
               8. Marcar carrinho como FINALIZADO
               9. Commit da transação

               Args:
                   db: Sessão do banco
                   usuario_id: ID do vendedor/usuário
                   cpf_cliente: CPF do cliente (opcional)
                   forma_pagamento: Forma de pagamento
                   percentual_desconto: Desconto percentual (0-100)

               Returns:
                   (sucesso: bool, mensagem: str, dados_venda: dict | None)
               """
        try:
            # 1. Buscar carrinho ativo
            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == usuario_id, Carrinho.status == 'ATIVO').first()

            if not carrinho:
                self.vendas_log.warning(f"Carrinho vazio para usuário {usuario_id}")
                return False, "Carrinho vazio", None

            if not carrinho.itens:
                self.vendas_log.warning(f"Carrinho sem itens: {carrinho.id_carrinho}")
                return False, "Carrinho vazio", None

            cliente_id = None
            if cpf_cliente:
                cpf_limpo = ''.join(filter(str.isdigit, cpf_cliente))
                cliente = db.query(Clientes).filter(Clientes.cpf == cpf_limpo).first()

                if not cliente:
                    self.vendas_log.warning(f"Cliente não encontrado: {cpf_cliente}")
                    return False, "Cliente não encontrado", None

                if not cliente.ativo:
                    self.vendas_log.warning(f"Cliente inativo: {cpf_cliente}")
                    return False, "Cliente inativo não pode realizar compras", None

                cliente_id = cliente.id_cliente

            from src.database.models import Usuarios
            vendedor = db.query(Usuarios).filter(Usuarios.id_usuario == usuario_id).first()

            vendedor_nome = vendedor.username if vendedor else None

            subtotal = float(carrinho.subtotal)

            venda = Vendas(data_hora=datetime.now(), subtotal=subtotal, desconto=0.0, total=subtotal,
                           forma_pagamento=forma_pagamento, cliente_id=cliente_id, vendedor_id=usuario_id,
                           vendedor_nome=vendedor_nome)

            if percentual_desconto > 0:
                if not 0 <= percentual_desconto <= 100:
                    return False, "Desconto deve estar entre 0 e 100%", None

                venda.aplicar_desconto(percentual_desconto)
                self.vendas_log.info(f"Desconto aplicado: {percentual_desconto}%")

            db.add(venda)
            db.flush()

            for item_carrinho in carrinho.itens:
                item_venda = ItemVenda(id_venda=venda.id_venda, produto_id=item_carrinho.produto_id,
                                       nome_produto=item_carrinho.produto.nome, quantidade=item_carrinho.quantidade,
                                       preco_unitario=item_carrinho.preco_unitario, subtotal=item_carrinho.subtotal
                                       )

                db.add(item_venda)

                sucesso, msg_estoque = self.estoque_controller.saida_estoque(db=db, id_produto=item_carrinho.produto_id,
                                                                             quantidade=item_carrinho.quantidade,
                                                                             usuario_id=usuario_id,
                                                                             venda_id=venda.id_venda
                                                                             )

                if not sucesso:
                    db.rollback()
                    self.vendas_log.error(
                        f"Erro na baixa de estoque: Produto {item_carrinho.produto_id} - {msg_estoque}"
                    )
                    return False, f"Erro no estoque: {msg_estoque}", None

            carrinho.status = 'FINALIZADO'

            db.commit()
            db.refresh(venda)

            self.vendas_log.info(
                f"Venda finalizada: ID {venda.id_venda} - "
                f"Vendedor: {vendedor_nome} (ID: {usuario_id}) - "
                f"Total: R$ {venda.total:.2f} - "
                f"Itens: {len(carrinho.itens)}"
            )

            venda_dados = {
                "id_venda": venda.id_venda,
                "total": float(venda.total),
                "subtotal": float(venda.subtotal),
                "desconto": float(venda.desconto),
                "forma_pagamento": venda.forma_pagamento,
                "data_hora": venda.data_hora.isoformat(),
                "vendedor_nome": venda.vendedor_nome,
                "total_itens": len(carrinho.itens)
            }

            return True, f"Venda finalizada com sucesso! ID: {venda.id_venda}", venda_dados

        except IntegrityError as ie:
            db.rollback()
            self.vendas_log.exception("Erro de integridade ao finalizar venda")
            return False, "Erro de integridade no banco de dados", None

        except Exception as e:
            db.rollback()
            self.vendas_log.exception(f"Erro ao finalizar venda: {e}")
            return False, "Erro interno ao processar venda", None

    def buscar_venda(self, db: Session, id_venda: int) -> Optional[Vendas]:
        """
        Busca venda por ID

        Returns:
            Venda com itens carregados ou None
        """
        try:
            venda = db.query(Vendas).filter(
                Vendas.id_venda == id_venda
            ).first()

            return venda

        except Exception as e:
            self.vendas_log.exception(f"Erro ao buscar venda {id_venda}")
            return None

    def cancelar_venda(self, db: Session, id_venda: int, motivo: str, usuario_id: int) -> Tuple[bool, str]:
        """
        Cancela uma venda e devolve itens ao estoque

        ⚠️ ATENÇÃO: Operação sensível! Requer permissão de admin/gerente

        Args:
            db: Sessão do banco
            id_venda: ID da venda a cancelar
            motivo: Motivo do cancelamento
            usuario_id: ID do usuário que está cancelando

        Returns:
            (sucesso: bool, mensagem: str)
        """
        try:
            # Buscar venda
            venda = db.query(Vendas).filter(Vendas.id_venda == id_venda).first()

            if not venda:
                return False, "Venda não encontrada"

            for item in venda.itens:
                produto = db.query(Produtos).filter(Produtos.codigo == item.produto_id).first()

                if produto:
                    estoque_anterior = produto.quantidade_estoque
                    produto.quantidade_estoque += item.quantidade

                    movimentacao = MovimentacaoEstoque(
                        produto_id=item.produto_id,
                        tipo='AJUSTE',
                        quantidade=item.quantidade,
                        estoque_anterior=estoque_anterior,
                        estoque_posterior=produto.quantidade_estoque,
                        usuario_id=usuario_id,
                        venda_id=id_venda,
                        observacao=f"Cancelamento de venda - Motivo: {motivo}"
                    )

                    db.add(movimentacao)

            carrinho = db.query(Carrinho).filter(Carrinho.usuario_id == venda.vendedor_id,
                                                 Carrinho.status == 'FINALIZADO').order_by(
                Carrinho.atualizado_em.desc()).first()

            if carrinho:
                carrinho.status = 'CANCELADO'

            db.commit()

            self.vendas_log.warning(
                f"VENDA CANCELADA: ID {id_venda} - "
                f"Usuário: {usuario_id} - Motivo: {motivo}"
            )

            return True, "Venda cancelada e itens devolvidos ao estoque"

        except Exception as e:
            db.rollback()
            self.vendas_log.exception(f"Erro ao cancelar venda {id_venda}")
            return False, f"Erro: {e}"

    def listar_vendas(self, db: Session, vendedor_id: Optional[int] = None, cliente_id: Optional[int] = None,
                      data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None,
                      limite: int = 100) -> list:
        """
        Lista vendas com filtros opcionais

        Args:
            db: Sessão do banco
            vendedor_id: Filtrar por vendedor
            cliente_id: Filtrar por cliente
            data_inicio: Data inicial
            data_fim: Data final
            limite: Máximo de resultados

        Returns:
            Lista de vendas
        """
        try:
            query = db.query(Vendas)

            if vendedor_id:
                query = query.filter(Vendas.vendedor_id == vendedor_id)

            if cliente_id:
                query = query.filter(Vendas.cliente_id == cliente_id)

            if data_inicio:
                query = query.filter(Vendas.data_hora >= data_inicio)

            if data_fim:
                query = query.filter(Vendas.data_hora <= data_fim)

            vendas = query.order_by(Vendas.data_hora.desc()).limit(limite).all()

            return vendas

        except Exception as e:
            self.vendas_log.exception("Erro ao listar vendas")
            return []

    def obter_estatisticas_vendas(self, db: Session, vendedor_id: Optional[int] = None,
                                  data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None) -> dict:
        """
        Retorna estatísticas de vendas

        Args:
            db: Sessão do banco
            vendedor_id: Filtrar por vendedor (opcional)
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)

        Returns:
            Dicionário com estatísticas
        """
        try:
            from sqlalchemy import func

            query = db.query(
                func.count(Vendas.id_venda).label('total_vendas'),
                func.sum(Vendas.total).label('valor_total'),
                func.avg(Vendas.total).label('ticket_medio'),
                func.sum(Vendas.desconto).label('total_descontos')
            )

            # Aplicar filtros
            if vendedor_id:
                query = query.filter(Vendas.vendedor_id == vendedor_id)

            if data_inicio:
                query = query.filter(Vendas.data_hora >= data_inicio)

            if data_fim:
                query = query.filter(Vendas.data_hora <= data_fim)

            resultado = query.first()

            return {
                "total_vendas": resultado.total_vendas or 0,
                "valor_total": float(resultado.valor_total or 0),
                "ticket_medio": float(resultado.ticket_medio or 0),
                "total_descontos": float(resultado.total_descontos or 0)
            }

        except Exception:
            self.vendas_log.exception("Erro ao obter estatísticas")
            return {
                "total_vendas": 0,
                "valor_total": 0,
                "ticket_medio": 0,
                "total_descontos": 0
            }
