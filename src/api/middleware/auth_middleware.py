from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.services.security import JWTHandler

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
       Dependency para obter usuário atual do token

    Usage:
        @router.get("/perfil")
        async def meu_perfil(user: dict = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials
    payload = JWTHandler.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido ou expirado",
                            headers={"WWW-Authenticate": "Bearer"})

    return JWTHandler.verify_token(token, token_type="access")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency que requer permissão de admin

    Usage:
        @router.delete("/usuario/{user_id}")
        async def deletar_usuario(user_id: int, admin: dict = Depends(require_admin)):
            # Apenas admins podem acessar
    """
    if user.get('tipo_usuario') != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Permissão negada. Apenas administradores podem acessar este recurso")
    return user


def require_admin_or_gerente(user: dict = Depends(get_current_user)) -> dict:
    """Requer permissão de admin ou gerente"""
    if user.get('tipo_usuario') not in ['admin', 'gerente']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada. Requer permissão de administrador ou gerente"
        )
    return user


def require_vendedor_or_above(user: dict = Depends(get_current_user)) -> dict:
    """Requer permissão de vendedor, gerente ou admin"""
    if user.get('tipo_usuario') not in ['admin', 'gerente', 'vendedor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada. Apenas vendedores podem acessar este recurso"
        )
    return user
