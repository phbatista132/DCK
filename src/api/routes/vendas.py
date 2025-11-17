from fastapi import APIRouter, HTTPException, status, Depends, Path
from src.controllers.venda_controller import VendaController
from src.api.schemas import FinalizarVendaResponse, FinalizarVendaRequest, ItemCarrinhoResponse, ItemCarrinhoRequest, \
    CarrinhoResponse, AlterarQuantidadeRequest
from src.api.middleware import require_vendedor_or_above, require_admin_or_gerente
from src.database import get_db
from src.utils.logKit import get_logger
from sqlalchemy.orm import Session

vendas_router = APIRouter(prefix="/sales", tags=["sales"])
endpoint_vendas_log = get_logger("LoggerVendas", "WARNING")


def get_venda_controller() -> VendaController:
    return VendaController()


@vendas_router.post("/cart/items", status_code=status.HTTP_201_CREATED, summary="Adicionar item ao carrinho")
async def adicionar_ao_carrinho(item: ItemCarrinhoRequest,
                                user: dict = Depends(require_vendedor_or_above),
                                controller: VendaController = Depends(get_venda_controller),
                                db: Session = Depends(get_db)):
    """
    ## Adiciona um produto ao carrinho de compras

    ### Fluxo:
    1. Valida se produto existe e está ativo
    2. Verifica disponibilidade em estoque
    3. Cria reserva temporária (30 minutos)
    4. Adiciona ao carrinho

    ### Regras:
    - ✅ Produto deve estar ativo
    - ✅ Estoque deve ter quantidade disponível
    - ✅ Reserva expira em 30 minutos

    ### Exemplo:
    ```bash
    curl -X POST "http://api/sales/cart/items" \\
         -H "Content-Type: application/json" \\
         -d '{"produto_id": 1, "quantidade": 2}'
    ```
    """
    try:
        endpoint_vendas_log.info(
            f"Adicionando ao carrinho - Produto: {item.produto_id}, Qtd: {item.quantidade}"
        )

        sucesso, resultado = controller.adicionar_item_carrinho(db=db, produto_id=item.produto_id,
                                                                quantidade=item.quantidade,
                                                                usuario_id=user['user_id'])

        if not sucesso:
            if "não encontrado" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=resultado
                )

            elif "desabilitado" in resultado.lower() or "desativado" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Produto desativado"
                )

            elif "indisponivel" in resultado.lower() or "insuficiente" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Estoque insuficiente"
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado
                )
        return {
            "sucess": True,
            "message": resultado,
            "produto_id": item.produto_id,
            "quantidade": item.quantidade,
            "vendedor": user['username']
        }
    except HTTPException:
        raise
    except Exception as e:
        endpoint_vendas_log.exception("Erro ao adicionar item ao carrinho")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao adicionar item ao carrinho"
        )


@vendas_router.get("/cart", status_code=status.HTTP_200_OK, response_model=CarrinhoResponse,
                   dependencies=[Depends(require_vendedor_or_above)], summary="Visualizar carrinho")
async def ver_carrinho(controller: VendaController = Depends(get_venda_controller),
                       db: Session = Depends(get_db),
                       user: dict = Depends(require_vendedor_or_above)) -> CarrinhoResponse:
    """
    ## Retorna o carrinho atual com todos os itens

    ### Informações retornadas:
    - Lista de produtos no carrinho
    - Quantidade de cada produto
    - Preço unitário e subtotal
    - Total geral

    ### Exemplo:
    ```bash
    curl -X GET "http://api/sales/cart"
    ```
    """
    try:
        carrinho = controller.ver_carrinho(db=db, usuario_id=user['user_id'])

        if not carrinho:
            return CarrinhoResponse(
                success=True,
                total_itens=0,
                subtotal=0.0,
                itens=[]
            )

        itens = []
        for item in carrinho.itens:
            itens.append(ItemCarrinhoResponse(
                produto_id=item.produto_id,
                nome=item.produto.nome,
                quantidade=item.quantidade,
                preco_unitario=float(item.preco_unitario),
                subtotal=float(item.subtotal)
            ))

        return CarrinhoResponse(
            success=True,
            total_itens=len(itens),
            subtotal=float(carrinho.subtotal),
            itens=itens
        )

    except Exception as e:
        endpoint_vendas_log.exception("Erro ao visualizar carrinho")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar carrinho"
        )


@vendas_router.delete("/cart/items/{produto_id}", status_code=status.HTTP_200_OK, summary="Remover item do carrinho")
async def remover_do_carrinho(produto_id: int = Path(..., gt=0, description="ID do produto"),
                              db: Session = Depends(get_db),
                              controller: VendaController = Depends(get_venda_controller),
                              user: dict = Depends(require_vendedor_or_above)):
    """
    ## Remove um produto do carrinho

    ### Fluxo:
    1. Localiza item no carrinho
    2. Libera reserva de estoque
    3. Remove item

    ### Exemplo:
    ```bash
    curl -X DELETE "http://api/sales/cart/items/1"
    ```
    """
    try:
        endpoint_vendas_log.info(f"User {user['username']} removendo produto {produto_id}")

        sucesso, resultado = controller.remover_item_carrinho(db=db, produto_id=produto_id, usuario_id=user['user_id'])

        if not sucesso:
            if "não encontrado" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item não está no carrinho"
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado
                )

        return {
            "success": True,
            "message": resultado,
            "produto_id": produto_id
        }

    except HTTPException:
        raise
    except Exception:
        endpoint_vendas_log.exception(f"Erro ao remover item {produto_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover item"
        )


@vendas_router.patch("/cart/items/{produto_id}", status_code=status.HTTP_200_OK,
                     summary="Alterar quantidade de item no carrinho")
async def alterar_quantidade_carrinho(
        produto_id: int = Path(..., gt=0, description="ID do produto"),
        alteracao: AlterarQuantidadeRequest = ...,
        db: Session = Depends(get_db),
        user: dict = Depends(require_vendedor_or_above),
        controller: VendaController = Depends(get_venda_controller)):
    """
    ## Altera a quantidade de um produto no carrinho

    ### Fluxo:
    - **Aumentar**: Tenta reservar mais estoque
    - **Diminuir**: Libera parte da reserva

    ### Validações:
    - Nova quantidade deve ser maior que zero
    - Estoque deve ter disponibilidade (se aumentar)

    ### Exemplo:
    ```bash
    curl -X PATCH "http://api/sales/cart/items/1" \\
         -H "Content-Type: application/json" \\
         -d '{"nova_quantidade": 5}'
    ```
    """
    try:
        endpoint_vendas_log.info(
            f"User {user['username']} alterando quantidade - "
            f"Produto: {produto_id}, Nova qtd: {alteracao.nova_quantidade}"
        )

        sucesso, resultado = controller.alterar_quantidade_carrinho(
            db=db,
            produto_id=produto_id,
            nova_quantidade=alteracao.nova_quantidade,
            usuario_id=user['user_id'])

        if not sucesso:
            if "não encontrado" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item não está no carrinho"
                )

            elif "insuficiente" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Estoque insuficiente para a quantidade solicitada"
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado
                )

        return {
            "success": True,
            "message": resultado,
            "produto_id": produto_id,
            "nova_quantidade": alteracao.nova_quantidade
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_vendas_log.exception(f"Erro ao alterar quantidade do produto {produto_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao alterar quantidade"
        )


@vendas_router.post("/checkout", status_code=status.HTTP_201_CREATED, response_model=FinalizarVendaResponse,
                    summary="Finalizar venda")
async def finalizar_venda(venda: FinalizarVendaRequest, controller: VendaController = Depends(get_venda_controller),
                          db: Session = Depends(get_db),
                          user: dict = Depends(require_vendedor_or_above)) -> FinalizarVendaResponse:
    """
    ## Finaliza a venda e processa pagamento

    ### Fluxo:
    1. Valida cliente (se CPF fornecido)
    2. Aplica desconto (se houver)
    3. Gera ID da venda
    4. Persiste venda e itens
    5. Realiza baixa definitiva no estoque
    6. Limpa carrinho

    ### Validações:
    - Carrinho não pode estar vazio
    - Cliente deve estar ativo (se CPF fornecido)
    - Forma de pagamento válida
    - Desconto entre 0-100%

    ### Exemplo:
    ```bash
    curl -X POST "http://api/sales/checkout" \\
         -H "Content-Type: application/json" \\
         -d '{
           "cpf_cliente": "12345678900",
           "forma_pagamento": "Credito",
           "percentual_desconto": 10.0
         }'
    ```
    """
    try:
        endpoint_vendas_log.info(
            f"Finalizando venda - Cliente: {venda.cpf_cliente or 'Sem CPF'}, "
            f"Pagamento: {venda.forma_pagamento}, Desconto: {venda.percentual_desconto}%"
        )

        sucesso, resultado, dados_venda = controller.finalizar_venda(
            db=db,
            usuario_id=user['user_id'],
            cpf_cliente=venda.cpf_cliente,
            forma_pagamento=venda.forma_pagamento,
            percentual_desconto=venda.percentual_desconto,
        )

        if not sucesso:
            if "vazio" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Carrinho vazio"
                )

            elif "não encontrado" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )

            elif "inativo" in resultado.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cliente inativo não pode realizar compras"
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado
                )

        endpoint_vendas_log.info(
            f"Venda finalizada com sucesso - "
            f"ID: {dados_venda['id_venda']}, "
            f"Total: R$ {dados_venda['total']:.2f}"
        )
        return FinalizarVendaResponse(
            success=True,
            message="Venda finalizada com sucesso",
            id_venda=dados_venda['id_venda'],
            total=dados_venda['total'],
            desconto_aplicado=dados_venda.get('desconto', 0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        endpoint_vendas_log.exception("Erro ao finalizar venda")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar venda"
        )


@vendas_router.delete(
    "/cart",
    status_code=status.HTTP_200_OK,
    summary="Cancelar venda e limpar carrinho"

)
async def cancelar_venda(controller: VendaController = Depends(get_venda_controller),
                         db: Session = Depends(get_db),
                         user: dict = Depends(require_vendedor_or_above)):
    """
    ## Cancela a venda atual e limpa o carrinho

    ### Fluxo:
    1. Libera todas as reservas de estoque
    2. Limpa carrinho completamente

    ### Quando usar:
    - Cliente desistiu da compra
    - Necessário recomeçar venda
    - Timeout de sessão

    ### Exemplo:
    ```bash
    curl -X DELETE "http://api/sales/cart"
    ```
    """
    try:
        endpoint_vendas_log.info("Cancelando venda e limpando carrinho")

        sucesso, resultado = controller.cancelar_carrinho(db=db, usuario_id=user['user_id'])

        if not sucesso:
            if "vazio" in resultado.lower():
                return {
                    "success": True,
                    "message": "Carrinho já estava vazio"
                }

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado
                )

        return {
            "success": True,
            "message": resultado
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_vendas_log.exception("Erro ao cancelar venda")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao cancelar venda")
