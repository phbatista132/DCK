from typing import Optional
from fastapi import APIRouter, status, HTTPException, Query, Depends
from src.api.schemas.produto_schema import ProdutoUpdate
from src.controllers import ProdutoController
from src.utils.logKit import get_logger
from src.api.schemas import ProdutoCreated
from src.api.middleware import require_admin_or_gerente
from src.database.connection import get_db
from sqlalchemy.orm import Session

produtos_router = APIRouter(prefix="/products", tags=["products"])
endpoint_produtos_log = get_logger("LoggerProduto", "WARNING")


def get_produto_controller() -> ProdutoController:
    """Dependency para obter instância do EstoqueController"""
    return ProdutoController()


@produtos_router.post("/", status_code=status.HTTP_201_CREATED, summary="Cadastra novo produto", )
async def cadastrar_produto(produto: ProdutoCreated, user: dict = Depends(require_admin_or_gerente),
                            db: Session = Depends(get_db),
                            controller: ProdutoController = Depends(get_produto_controller)):
    """
    Cadastra um novo produto no sistema

    Validações automáticas:
    - Valida casas decimais
    - Valida quantidade de produtos maior do 0
    - Produto nao duplicado

    """
    try:
        resultado = controller.cadastrar_produto(db, **produto.model_dump())

        if "sucesso" in resultado:
            return {"message": resultado}
        else:
            raise HTTPException(status_code=409, detail=resultado)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_produtos_log.exception(f"Erro ao cadastrar produto: {produto}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao cadastrar produto: {str(e)}")


@produtos_router.patch("/{id_produto}", status_code=status.HTTP_200_OK)
async def atualizar_produto(id_produto: int, produto: ProdutoUpdate,
                            db: Session = Depends(get_db), user: dict = Depends(require_admin_or_gerente),
                            controller: ProdutoController = Depends(get_produto_controller)):
    """
    Editar dados de um produto no sistema

    Campos editáveis:
    - Nome
    - Modelo
    - valor
    - vlr_compra

    OBS: Apenas os campos editaveis são atualizados
    """

    try:
        dados_atualizados = produto.model_dump(exclude_unset=True, exclude_none=True)

        if not dados_atualizados:
            raise HTTPException(status_code=400, detail="Nenhum produto atualizado")

        resultado = controller.editar_produto(db, id_produto, **dados_atualizados)
        if "sucesso" in resultado:
            return {"message": resultado}
        elif "não encontrado" in resultado:
            endpoint_produtos_log.warning(f"Produto: {id_produto} não encontrado")
            raise HTTPException(status_code=404, detail=resultado)
        else:
            endpoint_produtos_log.warning("Não foi possivel alterar produto")
            raise HTTPException(status_code=409, detail="Não foi possivel editar o produto")

    except HTTPException:
        raise
    except Exception as e:
        endpoint_produtos_log.error("Erro ao editar produto")
        raise HTTPException(status_code=500, detail=str(e))


@produtos_router.get("/search", status_code=status.HTTP_200_OK)
async def buscar_produto(db: Session = Depends(get_db),
                         nome: Optional[str] = Query(None, description="Buscar por nome"),
                         categoria: Optional[str] = Query(None, description="Buscar por categoria"),
                         modelo: Optional[str] = Query(None, description="Buscar por modelo"),
                         controller: ProdutoController = Depends(get_produto_controller)
                         ):
    """
    Buscar produto por coluna e dado

    :returns
        Retorna o produto formatado,

    :exception
        404 produto não encontrado
    """
    try:

        if nome:
            resultado = controller.busca_produto(db, 'nome', nome)
        elif categoria:
            resultado = controller.filtro_categoria(db, categoria)
        elif modelo:
            resultado = controller.busca_produto(db, 'modelo', modelo)
        else:
            raise HTTPException(status_code=400, detail="Forneça ao menos um filtro:  nome, categoria ou modelo")

        if "não localizado" in resultado:
            return {"database": [], "message": "Nenhum produto encontrado"}

        return {'database': resultado}

    except HTTPException:
        raise
    except Exception as e:
        endpoint_produtos_log.error("Erro ao buscar produto")
        raise HTTPException(status_code=500, detail=str(e))


@produtos_router.delete("/{id_produto}", status_code=status.HTTP_202_ACCEPTED)
async def desabilitar_produto(id_produto: int, db:Session = Depends(get_db), controller: ProdutoController = Depends(get_produto_controller),
                              user: dict = Depends(require_admin_or_gerente)):
    """
    Desabilitar produto (soft delete)

    O produto não é removido, apenas marcado como inativo.
    Produtos inativos não aparecem em buscas.
    """
    try:
        resultado = controller.desabilitar_produto(db, id_produto)

        if "sucesso" in resultado:
            return {"message": resultado,
                    "id_produto": id_produto
                    }
        elif "não encontrado" in resultado or "não localizado" in resultado:
            endpoint_produtos_log.warning(f"Produto: {id_produto} não localizado")
            raise HTTPException(status_code=404, detail=resultado)
        else:
            raise HTTPException(status_code=400, detail=resultado)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_produtos_log.error(f"Erro ao desabilitar produto: {id_produto}")
        raise HTTPException(status_code=500, detail=str(e))
