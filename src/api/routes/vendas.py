from fastapi import APIRouter, HTTPException, status, Depends, Path
from src.controllers.venda_controller import VendaController
from src.api.schemas import FinalizarVendaResponse, FinalizarVendaRequest, ItemCarrinhoResponse, ItemCarrinhoRequest, \
    CarrinhoResponse, AlterarQuantidadeRequest
from src.api.middleware import require_vendedor_or_above, require_admin_or_gerente
from src.utils.logKit import get_logger

vendas_router = APIRouter(prefix="/sales", tags=["sales"])
endpoint_vendas_log = get_logger("LoggerVendas", "WARNING")


def get_venda_controller() -> VendaController:
    return VendaController()


@vendas_router.post("/cart/items", status_code=status.HTTP_201_CREATED, summary="Adicionar item ao carrinho")
async def adicionar_ao_carrinho(item: ItemCarrinhoRequest,
                                user: dict = Depends(require_vendedor_or_above),
                                controller: VendaController = Depends(get_venda_controller)
                                ):
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

        resultado = controller.adicionar_item(item.produto_id, item.quantidade, user_id=user['user_id'])

        if "adicionado" in resultado.lower() or "sucesso" in resultado.lower():
            return {
                "success": True,
                "message": resultado,
                "produto_id": item.produto_id,
                "quantidade": item.quantidade,
                "vendedor": user['username']
            }

        elif "não encontrado" in resultado.lower():
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
        carrinho = controller.ver_carinho(user['user_id'])

        if not carrinho:
            return CarrinhoResponse(
                success=True,
                total_itens=0,
                subtotal=0.0,
                itens=[]
            )

        itens = [ItemCarrinhoResponse(**item) for item in carrinho]
        subtotal = sum(item.subtotal for item in itens)

        return CarrinhoResponse(
            success=True,
            total_itens=len(itens),
            subtotal=subtotal,
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

        resultado = controller.remover_item(produto_id, user['user_id'])

        if "removido" in resultado.lower() or "sucesso" in resultado.lower():
            return {
                "success": True,
                "message": resultado,
                "produto_id": produto_id
            }

        elif "não encontrado" in resultado.lower() or "não encotrado" in resultado.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não está no carrinho"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado
            )

    except HTTPException:
        raise
    except Exception as e:
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

        resultado = controller.alterar_quantidade(produto_id, alteracao.nova_quantidade, user['user_id'])

        if "sucesso" in resultado.lower() or "alterada" in resultado.lower():
            return {
                "success": True,
                "message": resultado,
                "produto_id": produto_id,
                "nova_quantidade": alteracao.nova_quantidade
            }

        elif "não encontrado" in resultado.lower():
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

        resultado = controller.finalizar_venda(
            cpf_cliente=venda.cpf_cliente,
            forma_pagamento=venda.forma_pagamento,
            percentual_desconto=venda.percentual_desconto,
            user_id=user['user_id'],
            username=user['username']
        )

        if "finalizada" in resultado.lower() or "sucesso" in resultado.lower():
            # Extrair ID e total da mensagem (formato: "Compra finalizada! ID: 42 | Total: R$ 6300.00")
            import re
            match_id = re.search(r'ID:\s*(\d+)', resultado)
            match_total = re.search(r'R\$\s*([\d,.]+)', resultado)

            id_venda = int(match_id.group(1)) if match_id else None
            total_str = match_total.group(1).replace(',', '.') if match_total else "0"
            total = float(total_str)

            desconto_aplicado = (total * venda.percentual_desconto / 100) if venda.percentual_desconto > 0 else 0

            return FinalizarVendaResponse(
                success=True,
                message="Venda finalizada com sucesso",
                id_venda=id_venda,
                total=total,
                desconto_aplicado=desconto_aplicado
            )

        elif "vazio" in resultado.lower():
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
                         user: dict = Depends(require_admin_or_gerente)):
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

        resultado = controller.cancelar_venda(user['user_id'])

        if "sucesso" in resultado.lower() or "cancelada" in resultado.lower():
            return {
                "success": True,
                "message": resultado
            }

        elif "vazio" in resultado.lower():
            return {
                "success": True,
                "message": "Carrinho já estava vazio"
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado
            )

    except HTTPException:
        raise
    except Exception as e:
        endpoint_vendas_log.exception("Erro ao cancelar venda")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao cancelar venda")
