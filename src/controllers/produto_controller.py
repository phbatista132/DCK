from typing import List
from src.database import Produtos
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.utils.logKit.config_logging import get_logger


class ProdutoController:
    def __init__(self):
        self.produto_log = get_logger("LoggerProdutoController", "DEBUG")

    def cadastrar_produto(self, db: Session, nome: str, modelo: str, categoria: str, valor: float,
                          quantidade_estoque: int, vlr_compra: float) -> str:
        """Cadastrar um produto"""

        try:
            if valor <= 0:
                return "Valor de venda deve ser maior que zero"

            if vlr_compra <= 0:
                return "Valor de compra deve ser maior que zero"

            if quantidade_estoque < 0:
                return "Quantidade de estoque não pode ser negativa"

            if valor <= vlr_compra:
                return "Valor de venda deve ser maior que valor de compra"

            produto = Produtos(
                nome=nome,
                modelo=modelo,
                categoria=categoria,
                quantidade_estoque=quantidade_estoque,
                valor=valor,
                vlr_compra=vlr_compra
            )
            db.add(produto)
            db.commit()
            db.refresh(produto)
            self.produto_log.info(f"Produto: {nome} cadastrado com sucesso")
            return "Produto cadastrado com sucesso"
        except IntegrityError:
            db.rollback()
            self.produto_log.warning(f"Produto: {nome} ja existente")
            return "Produto ja cadastrado"
        except Exception:
            db.rollback()
            self.produto_log.exception(f"Erro ao cadastrar produto")
            return "Erro interno ao cadastrar produto"

    def editar_produto(self, db: Session, id_produto, **kwargs) -> str:
        """
        Edita produto (whitelist: nome, modelo, categoria, valor, vlr_compra, quantidade_estoque)

        Uso:
            editar_produto(1, nome="Notebook Dell", valor=3500.0)
        """
        try:
            coluna_editaveis = ['nome', 'modelo', 'valor', 'vlr_compra']

            for coluna in kwargs.keys():
                if coluna not in coluna_editaveis:
                    self.produto_log.warning(f'Campo: {coluna} não permitido para edição')
                    return "Campo não pode ser editado"

            if 'valor' in kwargs and kwargs['valor'] <= 0:
                return "Valor de venda deve ser maior que zero"

            if 'vlr_compra' in kwargs and kwargs['vlr_compra'] <= 0:
                return "Valor de compra deve ser maior que zero"

            produto = db.query(Produtos).filter(Produtos.codigo == id_produto).first()

            if not produto:
                return "produto não localizado"

            for key, valor in kwargs.items():
                setattr(produto, key, valor)

            db.commit()

            self.produto_log.info(f"Produto {id_produto} editado: {kwargs} com sucesso")
            return "Produto editado com sucesso"

        except Exception:
            self.produto_log.exception(f'Erro ao editar produto {id_produto}')
            return f"Erro interno ao editar produto"

    def busca_produto(self, db: Session, coluna: str, dado_busca: str) -> str | List:
        """Busca produtos por coluna"""
        try:
            if coluna == 'nome':
                produtos = db.query(Produtos).filter(
                    Produtos.nome == dado_busca,
                    Produtos.ativo == True
                ).all()
            elif coluna == 'modelo':
                produtos = db.query(Produtos).filter(
                    Produtos.modelo == dado_busca,
                    Produtos.ativo == True
                ).all()
            elif coluna == 'categoria':
                produtos = db.query(Produtos).filter(
                    Produtos.categoria == dado_busca,
                    Produtos.ativo == True
                ).all()
            else:
                return "Coluna não localizada"

            if not produtos:
                return "Dado não localizado"

            resultado = [
                f"ID:{p.codigo} | Produto: {p.nome} | Modelo {p.modelo} | Estoque: {p.quantidade_estoque} | Valor: {p.valor}"
                for p in produtos
            ]

            return resultado

        except Exception as e:
            self.produto_log.exception(f"Erro ao buscar dado '{dado_busca}'")
            return f'Erro ao buscar: {e}'

    def desabilitar_produto(self, db: Session, idbusca: int) -> str:
        """Desativa produto (soft delete)"""
        try:
            produto = db.query(Produtos).filter(Produtos.codigo == idbusca).first()

            if not produto:
                return "Produto não localizado"

            produto.ativo = False
            db.commit()
            self.produto_log.info(f"Produto {idbusca} ({produto.nome}) desativado")
            return "Produto desativado com sucesso"

        except Exception as e:
            db.rollback()
            self.produto_log.exception(f"Erro ao deletar produto: {idbusca}")
            return f'Falha ao desativar: {e}'

    def filtro_categoria(self, db: Session, categoria: str) -> str:
        """Filtra produtos por categoria"""
        try:
            produtos = db.query(Produtos).filter(Produtos.categoria == categoria, Produtos.ativo.is_(True)).all()

            if not produtos:
                return f"Nenhum produto encontrado na categoria: {categoria}"

            resultado = [
                f"Produto: {p.nome} | Modelo: {p.modelo} | "
                f"Categoria: {p.categoria} | Valor: R$ {p.valor:.2f} | "
                f"Estoque: {p.quantidade_estoque}"
                for p in produtos
            ]

            self.produto_log.info(f"Encontrados {len(resultado)} produtos")
            return "\n".join(resultado)

        except Exception as e:
            self.produto_log.warning("Erro ao filtrar categoria")
            return f'Erro ao filtrar: {e}'

    def contar_produtos(self, db: Session) -> int:
        try:
            qtd_produtos = db.query(Produtos).filter(Produtos.ativo.is_(True)).count()

            return qtd_produtos
        except Exception as e:
            self.produto_log.exception(f"Erro ao verificar prdutos: {e}")
            return 0