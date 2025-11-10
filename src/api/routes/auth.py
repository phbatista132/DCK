from fastapi import APIRouter, HTTPException, status, Depends, Query
from src.controllers import AuthController
from src.api.schemas.auth_schema import (
    UsuarioRegistro, UsuarioLogin, TokenResponse,
    RefreshTokenRequest, AlterarSenhaRequest, UsuarioResponse
)
from src.api.middleware.auth_middleware import get_current_user, require_admin
from typing import List, Optional

from src.utils.logKit import get_logger

auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])
endpoit_auth_log = get_logger("LoggerAuth", "WARNING")

def get_auth_controller():
    """Dependency para obter controller"""
    return AuthController()


@auth_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
async def registrar(
        usuario: UsuarioRegistro,
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Registra novo usuário no sistema

    ### Tipos de Usuário:
    - **cliente**: Acesso básico (padrão) - pode fazer compras
    - **vendedor**: Pode registrar vendas
    - **gerente**: Gerencia vendas e estoque
    - **admin**: Acesso total ao sistema

    ### Requisitos de Senha:
    - Mínimo 8 caracteres
    - 1 letra maiúscula
    - 1 letra minúscula
    - 1 número
    - 1 caractere especial (!@#$%^&*()_+-)

    ### Segurança:
    - Senha armazenada com **bcrypt** (irreversível)
    - CPF e telefone criptografados com **Fernet** (reversível)
    - Username e email devem ser únicos

    **Nota:** Para criar admin/gerente, requer autenticação de admin
    (implementar lógica adicional se necessário)
    """
    sucesso, mensagem, dados = controller.registrar_usuario(**usuario.model_dump())

    if not sucesso:
        if "já está em uso" in mensagem or "já está cadastrado" in mensagem:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensagem)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensagem)

    return {
        "success": True,
        "message": mensagem,
        "user": dados
    }


@auth_router.post("/login", response_model=TokenResponse)
async def login(
        credenciais: UsuarioLogin,
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Autentica usuário e retorna tokens JWT

    ### Retorna:
    - **access_token**: Token de acesso (válido por 1 hora)
    - **refresh_token**: Token para renovar acesso (válido por 7 dias)
    - **user**: Dados do usuário autenticado

    ### Como usar o token:
    ```bash
    # Incluir em todas as requisições protegidas
    curl -X GET "http://api/perfil" \\
      -H "Authorization: Bearer {access_token}"
    ```

    ### Fluxo de Autenticação:
    1. Cliente faz login (recebe access_token + refresh_token)
    2. Usa access_token por 1 hora
    3. Quando expirar, usa refresh_token para obter novo access_token
    4. Refresh_token expira em 7 dias (fazer login novamente)
    """
    sucesso, mensagem, dados = controller.login(
        credenciais.username,
        credenciais.senha
    )

    if not sucesso:
        endpoit_auth_log.error(f"Erro validar login")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensagem,
            headers={"WWW-Authenticate": "Bearer"}
        )

    return TokenResponse(**dados)


@auth_router.post("/refresh", response_model=dict)
async def renovar_token(
        request: RefreshTokenRequest,
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Renova access_token usando refresh_token

    Use quando o access_token expirar (após 1 hora).
    O refresh_token é válido por 7 dias.

    ### Exemplo:
    ```bash
    curl -X POST "http://api/auth/refresh" \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "seu_refresh_token_aqui"}'
    ```
    """
    sucesso, mensagem, dados = controller.refresh_token(request.refresh_token)

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=mensagem
        )

    return {
        "success": True,
        **dados
    }


@auth_router.get("/me", response_model=UsuarioResponse)
async def perfil_usuario(
        user: dict = Depends(get_current_user),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Retorna dados do usuário autenticado

    Requer token válido no header:
    `Authorization: Bearer {access_token}`

    ### Retorna:
    - ID, username, email, nome completo
    - Tipo de usuário e status (ativo/inativo)
    - Data de cadastro e último acesso

    **Nota:** CPF e telefone NÃO são retornados (dados criptografados)
    """
    usuario = controller._buscar_usuario(user_id=user['user_id'])

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Remover dados sensíveis
    usuario_safe = {k: v for k, v in usuario.items()
                    if k not in ['senha_hash', 'cpf_criptografado', 'telefone_criptografado']}

    return UsuarioResponse(**usuario_safe)

@auth_router.put("/me/senha", status_code=status.HTTP_200_OK)
async def alterar_senha(
        request: AlterarSenhaRequest,
        user: dict = Depends(get_current_user),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Permite usuário alterar sua própria senha

    ### Validações:
    - Senha atual deve estar correta
    - Nova senha deve atender requisitos de segurança:
      - Mínimo 8 caracteres
      - 1 maiúscula, 1 minúscula, 1 número, 1 especial

    ### Exemplo:
    ```bash
    curl -X PUT "http://api/auth/me/senha" \\
      -H "Authorization: Bearer {token}" \\
      -H "Content-Type: application/json" \\
      -d '{
        "senha_atual": "SenhaAntiga123!",
        "nova_senha": "NovaSenha456!"
      }'
    ```
    """
    sucesso, mensagem = controller.alterar_senha(
        user['user_id'],
        request.senha_atual,
        request.nova_senha
    )

    if not sucesso:
        if "incorreta" in mensagem.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=mensagem
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensagem
            )

    return {
        "success": True,
        "message": mensagem
    }


@auth_router.get("/usuarios", response_model=List[UsuarioResponse])
async def listar_usuarios(
        tipo_usuario: Optional[str] = Query(
            None,
            pattern="^(admin|gerente|vendedor|cliente)$",
            description="Filtrar por tipo de usuário"
        ),
        incluir_inativos: bool = Query(False, description="Incluir usuários inativos"),
        admin: dict = Depends(require_admin),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Lista usuários do sistema (apenas admins)

    ### Filtros:
    - **tipo_usuario**: admin, gerente, vendedor, cliente
    - **incluir_inativos**: true/false

    ### Exemplo:
    ```bash
    # Listar apenas vendedores ativos
    curl -X GET "http://api/auth/usuarios?tipo_usuario=vendedor" \\
      -H "Authorization: Bearer {admin_token}"
    ```

    **Permissão:** Apenas administradores
    """
    usuarios = controller.listar_usuarios(
        tipo_usuario=tipo_usuario,
        incluir_inativos=incluir_inativos
    )

    return [UsuarioResponse(**u) for u in usuarios]


@auth_router.delete("/usuarios/{user_id}", status_code=status.HTTP_200_OK)
async def desativar_usuario(
        user_id: int,
        admin: dict = Depends(require_admin),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Desativa usuário (soft delete)

    Usuários desativados:
    - Não podem fazer login
    - Não aparecem em listagens (exceto com filtro)
    - Dados permanecem no sistema

    **Permissão:** Apenas administradores

    ### Exemplo:
    ```bash
    curl -X DELETE "http://api/auth/usuarios/5" \\
      -H "Authorization: Bearer {admin_token}"
    ```
    """
    # Não permitir admin desativar a si mesmo
    if user_id == admin['user_id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta"
        )

    sucesso, mensagem = controller.desativar_usuario(user_id)

    if not sucesso:
        if "não encontrado" in mensagem.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=mensagem
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensagem
            )

    return {
        "success": True,
        "message": mensagem
    }