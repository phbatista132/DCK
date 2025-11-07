from fastapi import APIRouter, status, HTTPException
from src.controllers import ProdutoController
from src.utils.logKit import get_logger
from src.api.schemas import ProdutoCreated

produtos_router = APIRouter(prefix="/products", tags=["products"])
endpoint_produtos_log = get_logger("produtos", "ERROR")

@produtos_router.post("/", status_code=status.HTTP_200_OK)
async def cadastrar_produto(produto: ProdutoCreated):
    """
    Cadastra um novo produto no sistema

    Validações automáticas:
    - Valida casas decimais
    - Valida quantidade de produtos maior do 0
    - Produto nao duplicado

    """
    try:
        controller = ProdutoController()
        resultado = controller.cadastrar_produto(**produto.model_dump())

        if "sucesso" in resultado:
            return {"message": resultado}
        else:
            raise HTTPException(status_code=400, detail=resultado)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_produtos_log.exception(f"Erro ao cadastrar produto: {produto}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao cadastrar produto: {str(e)}")

