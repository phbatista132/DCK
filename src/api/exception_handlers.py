from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from jwt.exceptions import InvalidTokenError


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Trata erros  de validação Pydantic"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"success": False,
                                                                   "message": "Dados invalidos",
                                                                   "errors": exc.errors()
                                                                   })


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Trata erros não esperados"""
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"success": False,
                                 "message": "Erro interno do servidor",
                                 "error_type": type(exc).__name__
                                 })

async def jwt_exception_handler(request: Request, exc: InvalidTokenError) -> JSONResponse:
    """Trata erros de JWT"""
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"success": False,
                                 "message": "Token invalido ou expirado",
                                 "error_type": "authentication_error"
                                 })