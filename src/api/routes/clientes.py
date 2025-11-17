from typing import List
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.utils.logKit.config_logging import get_logger
from fastapi import APIRouter, HTTPException, Query, status, Depends
from src.controllers.cliente_controller import ClienteController
from src.api.schemas import ClienteCreate, ClienteUpdate, ClienteResponse
from src.api.middleware import get_current_user, require_admin_or_gerente

cliente_router = APIRouter(prefix="/clients", tags=["clients"])
endpoint_cliente_log = get_logger("LoggerCliente", "WARNING")


def get_cliente_controller() -> ClienteController:
    return ClienteController()


@cliente_router.post("/register", status_code=status.HTTP_201_CREATED,
                     dependencies=[Depends(get_current_user)],
                     response_model=dict,
                     summary="Registrar novo cliente",
                     description="Cadastra um cliente no sistema")
async def cliente_register(cliente: ClienteCreate, db: Session = Depends(get_db),
                           controller: ClienteController = Depends(get_cliente_controller)):
    """
    Cadastra novo cliente no sistema

    Validações automaticas:
    - CPF valido (11 digitos)
    - Cliente Maior de 18 anos
    - CPF não duplicado
    """
    try:
        resultado = controller.cadastrar_cliente(db, **cliente.model_dump())

        if "sucesso" in resultado:
            return {
                "message": resultado,
                "data": {
                    "nome": cliente.nome
                }
            }
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=resultado)

    except HTTPException:
        raise
    except  Exception as e:
        endpoint_cliente_log.exception(f"Erro ao cadastrar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao cadastrar cliente")


@cliente_router.get("/search", dependencies=[Depends(get_current_user)])
async def cliente_search(db: Session = Depends(get_db),
                         cpf: str = Query(..., min_length=11, max_length=14, description="CPF do cliente"),
                         controller: ClienteController = Depends(get_cliente_controller)):
    """
    Buscar cliente por CPF

    :returns:
        Cliente encontrado com todos os dados
    Raises:
        404: CLiente não encontrado
    """
    try:
        resultado = controller.buscar_cliente(db, cpf)
        if not resultado:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        endpoint_cliente_log.exception(f"Erro ao buscar cliente")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar cliente")


@cliente_router.put("/edit_registration", dependencies=[Depends(require_admin_or_gerente)])
async def cliente_edit_registration(cpf: str, cliente_update: ClienteUpdate, db: Session = Depends(get_db),
                                    controller: ClienteController = Depends(get_cliente_controller)):
    """
    Edita dados de contato do cliente

    Campos editáveis:
    - Telefone
    - Endereço

    Nota: Apenas os campos fornecidos serão atualizados
    """
    try:
        dados_atualizacao = cliente_update.model_dump(exclude_unset=True)

        if not dados_atualizacao:
            raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização")

        resultado = controller.editar_cadastro(db, cpf, **dados_atualizacao)

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


@cliente_router.delete("/disable", dependencies=[Depends(require_admin_or_gerente)])
async def cliente_disabled(cpf: str, db: Session = Depends(get_db),
                           controller: ClienteController = Depends(get_cliente_controller)):
    """
    Desativa cliente (soft delete)

    O cliente não é removido do sistema, apenas marcado como inativo.
    Cliente inativos não aparecem em listagem e não podem fazer compras
    """
    try:
        resultado = controller.desativar_cliente(db=db, cpf=cpf)

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


@cliente_router.get("", response_model=List[ClienteResponse],
                    dependencies=[Depends(get_current_user), Depends(require_admin_or_gerente)])
async def list_clients(
        skip: int = Query(0, ge=0, description="Numero de registros a pular"),
        limit: int = Query(100, ge=1, le=1000, description="Maximo de registros"),
        db: Session = Depends(get_db),
        controller: ClienteController = Depends(get_cliente_controller)
):
    """
    Lista todos os clientes ativos

    Parâmetros de paginação:
    - **skip**: Offset para paginação (padrão 0)
    - **limit**: Numero maximo de resultados (padrão: 100, Máx: 1000)

    """

    try:
        resultado = controller.listar_clientes(db)

        if isinstance(resultado, str):
            return []

        return resultado[skip: skip + limit]

    except Exception as e:
        endpoint_cliente_log.exception("Erro ao listar clientes")
        raise HTTPException(status_code=500, detail="Erro interno ao listar_clientes")
