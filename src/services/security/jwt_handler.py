from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import os


class JWTHandler:
    """Gerenciador  de tokens JWT"""

    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria token de acesso JWT

        Args:
            data: Dados a serem codificados(user_id, username, tipo_usuario)
            expires_delta: Tempo de expiração customizado

        Returns:
            Token JWT assinado
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })

        enconded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return enconded_jwt

    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        """Cria token de refresh"""

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def decode_token(cls, token: str) -> Optional[dict]:
        """Decode token de acesso JWT

        Returns:
             Payload do token ou None se invalido
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except ExpiredSignatureError:
            return {"error": "expired"}
        except InvalidTokenError:
            return {"error": "invalid"}

    @classmethod
    def verify_token(cls, token: str, token_type: str = "access") -> Optional[dict]:
        """Verifica se token é valido e do tipo correto"""

        payload = cls.decode_token(token)

        if payload.get("error") == "expired":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token expirado",
                                headers={"WWW-Authenticate": "Bearer"}
                                )

        if payload.get("error") == "invalid":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token inválido",
                                headers={"WWW-Authenticate": "Bearer"}
                                )

        if payload.get("type") != token_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Tipo de token inválido",
                                headers={"WWW-Authenticate": "Bearer"}
                                )

        return payload
