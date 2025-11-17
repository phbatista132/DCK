from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, status, HTTPException, Query, Depends, Path
from src.database.connection import get_db
from src.controllers import EstoqueController
from src.utils.logKit import get_logger
from src.api.schemas import EstoqueReposicaoResponse, EstoqueReposicaoRequest, DisponibilidadeResponse, ReservasResponse
from src.api.middleware import get_current_user, require_admin_or_gerente, require_vendedor_or_above


def get_estoque_controller() -> EstoqueController:
    """Dependency para obter instância do EstoqueController"""
    return EstoqueController()


estoque_router = APIRouter(prefix="/stock", tags=["stock"])
endpoint_estoque_log = get_logger("LoggerEstoque", "WARNING")


@estoque_router.put(
    "/{id_produto}/replenish",
    status_code=status.HTTP_200_OK,
    response_model=EstoqueReposicaoResponse,
    summary="Repor estoque de um produto"
)
async def repor_estoque(id_produto: int = Path(..., gt=0, description="ID do produto a ser reposto"),
                        db: Session = Depends(get_db),
                        reposicao: EstoqueReposicaoRequest = ...,
                        controller: EstoqueController = Depends(get_estoque_controller),
                        user: dict = Depends(require_admin_or_gerente)) -> EstoqueReposicaoResponse:
    """
    ## Repõe estoque de um produto ativo

    ### Regras de Negócio:
    - ✅ Apenas produtos **ativos** podem ter estoque reposto
    - ✅ Quantidade deve ser **maior que zero**
    - ✅ Produto deve existir no sistema

    ### Exemplo de Uso:
    ```bash
    curl -X PUT "http://api/stock/1/replenish" \\
         -H "Content-Type: application/json" \\
         -d '{"quantidade": 100}'
    ```
    """
    try:
        endpoint_estoque_log.info(
            f"Reposição solicitada - Produto: {id_produto}, Quantidade: {reposicao.quantidade}"
        )

        resultado = controller.repor_estoque(db, id_produto, reposicao.quantidade, usuario_id=user['user_id'])

        if "sucesso" in resultado.lower():
            return EstoqueReposicaoResponse(
                success=True,
                message=resultado,
                data={
                    "id_produto": id_produto,
                    "quantidade_adicionada": reposicao.quantidade
                }
            )

        elif "não localizado" in resultado.lower() or "não encontrado" in resultado.lower():
            endpoint_estoque_log.warning(f"Produto {id_produto} não encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto {id_produto} não encontrado no sistema"
            )

        elif "desativado" in resultado.lower():
            endpoint_estoque_log.warning(f"Tentativa de repor produto desativado: {id_produto}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto desativado. Não é possível repor estoque"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=resultado
            )

    except HTTPException:
        raise
    except Exception as e:
        endpoint_estoque_log.exception(f"Erro ao repor estoque do produto {id_produto}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar reposição"
        )


@estoque_router.get(
    "/reservations",
    status_code=status.HTTP_200_OK,
    response_model=ReservasResponse,
    summary="Consultar reservas de estoque"
)
async def obter_reservas_usuario(
        controller: EstoqueController = Depends(get_estoque_controller),
        db: Session = Depends(get_db),
        user: dict = Depends(get_current_user)) -> ReservasResponse:
    """
    ## Consulta informações sobre reservas de estoque

    ### Funcionalidade:
    - 🔍 **Sem filtro**: Retorna todas as reservas ativas
    - 🎯 **Com id_produto**: Retorna apenas reservas daquele produto

    ### ⚠️ Nota de Segurança:
    Este endpoint expõe informações internas.
    Em produção, deveria exigir autenticação de administrador.
    """
    try:
        resultado = controller.obter_reservas_usuario(db, user['user_id'])

        # Enriquecer dados com tempo restante
        reservas_enriquecidas = {}
        for pid, dados in resultado:
            expira_em_str = dados.get("expira_em")
            tempo_restante = None

            if expira_em_str:
                try:
                    expira_em = datetime.fromisoformat(expira_em_str)
                    tempo_restante = int((expira_em - datetime.now()).total_seconds() / 60)
                except Exception:
                    pass

            reservas_enriquecidas[str(pid)] = {
                "quantidade": dados.get("quantidade", 0),
                "expira_em": expira_em_str,
                "tempo_restante_minutos": tempo_restante
            }

        return ReservasResponse(
            success=True,
            total_reservas=len(reservas_enriquecidas),
            reservas=reservas_enriquecidas
        )

    except Exception as e:
        endpoint_estoque_log.exception("Erro ao obter informações de reservas")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar reservas"
        )


@estoque_router.get(
    "/{id_produto}/availability",
    status_code=status.HTTP_200_OK,
    response_model=DisponibilidadeResponse,
    summary="Verificar disponibilidade de produto"
)
async def verificar_disponibilidade(
        id_produto: int = Path(..., gt=0, description="ID do produto"),
        quantidade: int = Query(1, gt=0, description="Quantidade desejada"),
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        controller: EstoqueController = Depends(get_estoque_controller)
) -> DisponibilidadeResponse:
    """
    ## Verifica disponibilidade real de um produto

    Retorna disponibilidade considerando estoque reservado em carrinhos.

    ### Exemplo:
    ```bash
    curl -X GET "http://api/stock/1/availability?quantidade=10"
    ```
    """
    try:
        habilitado, msg_habilitado = controller.produto_habilitado(db, id_produto)

        if not habilitado:
            if "não localizado" in msg_habilitado.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Produto {id_produto} não encontrado"
                )

        disponivel, qtd_disponivel = controller.verificar_disponibilidade(db,
                                                                          id_produto,
                                                                          quantidade,
                                                                          user['usename'])

        return DisponibilidadeResponse(
            success=True,
            id_produto=id_produto,
            disponivel=disponivel,
            estoque_disponivel=qtd_disponivel,
            quantidade_solicitada=quantidade,
            produto_ativo=habilitado,
            message=f"{'Quantidade disponível' if disponivel else 'Estoque insuficiente'}"
        )

    except HTTPException:
        raise
    except Exception as e:
        endpoint_estoque_log.exception(f"Erro ao verificar disponibilidade")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao verificar disponibilidade"
        )
