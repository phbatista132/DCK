from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.controllers import AuthController
from src.api.schemas.auth_schema import (UsuarioRegistro, UsuarioLogin, TokenResponse, RefreshTokenRequest,
                                         AlterarSenhaRequest, UsuarioResponse)
from src.api.middleware.auth_middleware import get_current_user, require_admin
from src.database.connection import get_db
from typing import List, Optional
from src.utils.logKit import get_logger

limiter = Limiter(key_func=get_remote_address)
auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])
endpoint_auth_log = get_logger("LoggerAuth", "WARNING")


def get_auth_controller() -> AuthController:
    """Dependency para obter instância do controller"""
    return AuthController()


@limiter.limit('3/minute')
@auth_router.post("/register",
                  status_code=status.HTTP_201_CREATED,
                  response_model=dict,
                  summary="Registrar novo usuário",
                  description="Cadastra um novo usuário no sistema com validações de segurança")
async def registrar(request: Request, usuario: UsuarioRegistro, db: Session = Depends(get_db),
                    controller: AuthController = Depends(get_auth_controller)):
    """
    ## Registra novo usuário no sistema

    ### Tipos de Usuário:
    - **admin**: Acesso total ao sistema
    - **gerente**: Gerencia vendas e estoque
    - **vendedor**: Pode registrar vendas

    ### Requisitos de Senha:
    - Mínimo 8 caracteres
    - 1 letra maiúscula
    - 1 letra minúscula
    - 1 número
    - 1 caractere especial (!@#$%^&*()_+-)

    ### Segurança:
    - Senha armazenada com **bcrypt** (irreversível)
    - Username e email devem ser únicos

    ### Exemplo de requisição:
    ```json
    {
        "username": "joao.silva",
        "email": "joao@loja.com",
        "senha": "SenhaSegura123!",
        "nome_completo": "João Silva",
        "tipo_usuario": "vendedor"
    }
    ```
    """
    try:
        sucesso, mensagem, dados = controller.registrar_usuario(
            db=db,
            **usuario.model_dump()
        )

        if not sucesso:
            if "já está em uso" in mensagem or "já está cadastrado" in mensagem:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=mensagem
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=mensagem
                )

        return {
            "success": True,
            "message": mensagem,
            "user": dados
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro inesperado ao registrar usuário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar usuário"
        )


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário",
    description="Realiza login e retorna tokens JWT"
)
async def login(
        credenciais: UsuarioLogin,
        db: Session = Depends(get_db),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Autentica usuário e retorna tokens JWT

    ### Retorna:
    - **access_token**: Token de acesso (válido por 15 minutos)
    - **refresh_token**: Token para renovar acesso (válido por 7 dias)
    - **user**: Dados do usuário autenticado

    ### Como usar o token:
    ```bash
    # Incluir em todas as requisições protegidas
    curl -X GET "http://api/auth/me" \\
      -H "Authorization: Bearer {access_token}"
    ```

    ### Fluxo de Autenticação:
    1. Cliente faz login (recebe access_token + refresh_token)
    2. Usa access_token por 15 minutos
    3. Quando expirar, usa refresh_token para obter novo access_token
    4. Refresh_token expira em 7 dias (fazer login novamente)

    ### Exemplo de requisição:
    ```json
    {
        "username": "joao.silva",
        "senha": "SenhaSegura123!"
    }
    ```
    """
    try:
        sucesso, mensagem, dados = controller.login(
            db=db,
            username=credenciais.username,
            senha=credenciais.senha
        )

        if not sucesso:
            endpoint_auth_log.warning(
                f"Tentativa de login falhou para usuário: {credenciais.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=mensagem,
                headers={"WWW-Authenticate": "Bearer"}
            )

        endpoint_auth_log.info(f"Login bem-sucedido: {credenciais.username}")
        return TokenResponse(**dados)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro inesperado durante login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login"
        )


@auth_router.post(
    "/refresh",
    response_model=dict,
    summary="Renovar access token",
    description="Usa refresh_token para obter novo access_token"
)
async def renovar_token(
        request: RefreshTokenRequest,
        db: Session = Depends(get_db),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Renova access_token usando refresh_token

    Use quando o access_token expirar (após 15 minutos).
    O refresh_token é válido por 7 dias.

    ### Exemplo:
    ```bash
    curl -X POST "http://api/auth/refresh" \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "seu_refresh_token_aqui"}'
    ```

    ### Resposta:
    ```json
    {
        "success": true,
        "access_token": "novo_token_aqui",
        "token_type": "bearer"
    }
    ```
    """
    try:
        from src.services.security.jwt_handler import JWTHandler

        # Verificar e decodificar refresh token
        payload = JWTHandler.verify_token(request.refresh_token, token_type="refresh")

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado"
            )

        # Buscar usuário para verificar se ainda está ativo
        usuario = controller.buscar_usuario(db=db, user_id=payload['user_id'])

        if not usuario or not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou inativo"
            )

        # Gerar novo access token
        token_data = {
            "user_id": usuario.id_usuario,
            "username": usuario.username,
            "tipo_usuario": usuario.tipo_usuario
        }

        novo_access_token = JWTHandler.create_access_token(token_data)

        return {
            "success": True,
            "access_token": novo_access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro ao renovar token")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao renovar token"
        )


@auth_router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Obter perfil do usuário",
    description="Retorna dados do usuário autenticado"
)
async def perfil_usuario(
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
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

    ### Exemplo:
    ```bash
    curl -X GET "http://api/auth/me" \\
      -H "Authorization: Bearer {seu_token}"
    ```
    """
    try:
        usuario = controller.buscar_usuario(db=db, user_id=user['user_id'])

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Converter para dict removendo dados sensíveis
        usuario_dict = {
            'id_usuario': usuario.id_usuario,
            'username': usuario.username,
            'email': usuario.email,
            'nome_completo': usuario.nome_completo,
            'tipo_usuario': usuario.tipo_usuario,
            'ativo': usuario.ativo,
            'data_cadastro': usuario.data_cadastro.isoformat(),
            'ultimo_acesso': usuario.ultimo_acesso.isoformat() if usuario.ultimo_acesso else None
        }

        return UsuarioResponse(**usuario_dict)

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro ao buscar perfil do usuário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar perfil"
        )


@auth_router.put(
    "/me/senha",
    status_code=status.HTTP_200_OK,
    summary="Alterar senha",
    description="Permite usuário alterar sua própria senha"
)
async def alterar_senha(
        request: AlterarSenhaRequest,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
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
    try:
        sucesso, mensagem = controller.alterar_senha(
            db=db,
            user_id=user['user_id'],
            senha_atual=request.senha_atual,
            nova_senha=request.nova_senha
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

        endpoint_auth_log.info(f"Senha alterada com sucesso - User ID: {user['user_id']}")

        return {
            "success": True,
            "message": mensagem
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro ao alterar senha")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao alterar senha"
        )


@auth_router.get(
    "/usuarios",
    response_model=List[UsuarioResponse],
    summary="Listar usuários",
    description="Lista usuários do sistema (apenas admins)"
)
async def listar_usuarios(
        tipo_usuario: Optional[str] = Query(
            None,
            pattern="^(admin|gerente|vendedor)$",
            description="Filtrar por tipo de usuário"
        ),
        incluir_inativos: bool = Query(
            False,
            description="Incluir usuários inativos"
        ),
        admin: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Lista usuários do sistema (apenas admins)

    ### Filtros:
    - **tipo_usuario**: admin, gerente, vendedor
    - **incluir_inativos**: true/false

    ### Exemplo:
    ```bash
    # Listar apenas vendedores ativos
    curl -X GET "http://api/auth/usuarios?tipo_usuario=vendedor" \\
      -H "Authorization: Bearer {admin_token}"

    # Listar todos incluindo inativos
    curl -X GET "http://api/auth/usuarios?incluir_inativos=true" \\
      -H "Authorization: Bearer {admin_token}"
    ```

    **Permissão:** Apenas administradores
    """
    try:
        usuarios = controller.listar_usuarios(
            db=db,
            tipo_usuario=tipo_usuario,
            incluir_inativos=incluir_inativos
        )

        return [UsuarioResponse(**u) for u in usuarios]

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception("Erro ao listar usuários")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar usuários"
        )


@auth_router.delete(
    "/usuarios/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Desativar usuário",
    description="Desativa um usuário (soft delete)"
)
async def desativar_usuario(
        user_id: int,
        admin: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        controller: AuthController = Depends(get_auth_controller)
):
    """
    ## Desativa usuário (soft delete)

    Usuários desativados:
    - Não podem fazer login
    - Não aparecem em listagens (exceto com filtro)
    - Dados permanecem no sistema para auditoria

    **Permissão:** Apenas administradores

    ### Restrições:
    - Admin não pode desativar a si mesmo

    ### Exemplo:
    ```bash
    curl -X DELETE "http://api/auth/usuarios/5" \\
      -H "Authorization: Bearer {admin_token}"
    ```
    """
    try:
        # Não permitir admin desativar a si mesmo
        if user_id == admin['user_id']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode desativar sua própria conta"
            )

        sucesso, mensagem = controller.desativar_usuario(db=db, user_id=user_id)

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

        endpoint_auth_log.info(
            f"Usuário {user_id} desativado por admin {admin['username']}"
        )

        return {
            "success": True,
            "message": mensagem
        }

    except HTTPException:
        raise
    except Exception as e:
        endpoint_auth_log.exception(f"Erro ao desativar usuário {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao desativar usuário"
        )


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Fazer logout",
    description="Invalida token do usuário (implementação básica)"
)
async def logout(
        user: dict = Depends(get_current_user)
):
    """
    ## Faz logout do usuário

    ### Nota sobre implementação:
    Como estamos usando JWT stateless, não há invalidação real do token no servidor.
    O cliente deve:
    1. Remover o token do armazenamento local
    2. Parar de enviar o token nas requisições

    ### Para invalidação real de tokens:
    - Implementar blacklist de tokens (Redis)
    - Ou usar tokens com tempo de vida curto + refresh tokens

    ### Exemplo:
    ```bash
    curl -X POST "http://api/auth/logout" \\
      -H "Authorization: Bearer {token}"
    ```
    """
    endpoint_auth_log.info(f"Logout realizado - User: {user['username']}")

    return {
        "success": True,
        "message": "Logout realizado com sucesso. Remova o token do cliente."
    }
