from typing import List
from src.utils.logKit.config_logging import get_logger
from fastapi import APIRouter, HTTPException, Query, status
from src.controllers.cliente_controller import ClienteController
from src.api.schemas import ClienteCreate, ClienteUpdate, ClienteResponse


cliente_router = APIRouter(prefix="/clients", tags=["clients"])
endpoint_cliente_log = get_logger("endpoints", "ERROR")


@cliente_router.post("/", status_code=status.HTTP_201_CREATED)
async def cliente_register(cliente: ClienteCreate):
    """
    Cadastra novo cliente no sistema

    Validações automaticas:
    - CPF valido (11 digitos)
    - Cliente Maior de 18 anos
    - CPF não duplicado
    """
    try:
        controller = ClienteController()
        resultado = controller.cadastrar_cliente(**cliente.model_dump())

        if "sucesso" in resultado:
            return {
                "message": resultado,
                "data": {
                    "nome": cliente.nome
                }
            }
        else:
            raise HTTPException(status_code=400, detail=resultado)

    except HTTPException:
        raise
    except  Exception as e:
        endpoint_cliente_log.exception(f"Erro ao cadastrar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao cadastrar cliente")


@cliente_router.get("/search")
async def cliente_search(cpf: str = Query(..., min_length=11, max_length=14, description="CPF do cliente")):
    """
    Buscar cliente por CPF

    :returns:
        Cliente encontrado com todos os dados
    Raises:
        404: CLiente não encontrado
    """
    try:
        controller = ClienteController()
        resultado = controller.buscar_cliente(cpf)
        if not resultado:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        endpoint_cliente_log.exception(f"Erro ao buscar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar cliente")


@cliente_router.put("/edit_registration")
async def cliente_edit_registration(cpf: str, cliente_update: ClienteUpdate):
    """
    Edita dados de contato do cliente

    Campos editáveis:
    - Telefone
    - Endereço

    Nota: Apenas os campos fornecidos serão atualizados
    """
    try:

        controller = ClienteController()
        dados_atualizacao = cliente_update.model_dump(exclude_unset=True)

        if not dados_atualizacao:
            raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização")

        resultado = controller.editar_cadastro(cpf, **dados_atualizacao)

        if "sucesso" in resultado:
            return {
                "message": resultado
            }
        elif "não encontrado" in resultado:
            raise HTTPException(status_code=404, detail=resultado)

        else:
            raise HTTPException(status_code=400, detail=resultado)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_cliente_log.exception("Erro ao editar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao editar cliente")



@cliente_router.delete("/disable")
async def cliente_desabilitar(cpf: str):
    """
    Desativa cliente (soft delete)

    O cliente não é removido do sistema, apenas marcado como inativo.
    Cliente inativos não aparecem em listagem e não podem fazer compras
    """
    try:
        controller = ClienteController()
        resultado = controller.desativar_cliente(cpf)

        if "desativado" in resultado or "sucesso" in resultado:
            return {"message": resultado}

        elif "Não encontrado" in resultado:
            raise HTTPException(status_code=404, detail=resultado)
        else:
            raise HTTPException(status_code=400, detail=resultado)
    except HTTPException:
        raise
    except Exception as e:
        endpoint_cliente_log.exception(f"Erro desativar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao desativar cliente")

@cliente_router.get("", response_model=List[ClienteResponse])
async def cliente_listar_clientes(
    skip: int = Query(0, ge=0, description="Numero de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Maximo de registros")
):
    """
    Lista todos os clientes ativos

    Parâmetros de paginação:
    - **skip**: Offset para paginação (padrão 0)
    - **limit**: Numero maximo de resultados (padrão: 100, Máx: 1000)

    """

    try:
        clientes = ClienteController()
        resultado = clientes.listar_clientes()

        if isinstance(resultado, str):
            return []

        return resultado[skip: skip + limit]

    except Exception as e:
        endpoint_cliente_log.exception("Erro ao listar clientes")
        raise HTTPException(status_code=500, detail="Erro interno ao listar_clientes")

