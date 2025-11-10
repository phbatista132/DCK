from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from jwt import InvalidTokenError

from src.api.routes import clientes, produtos, vendas, estoque, auth
from src.api.exception_handlers import validation_exception_handler, jwt_exception_handler, generic_exception_handler


app = FastAPI(title="API Sistema de Loja", description="API REST para gerenciamento de loja", version="1.0.0")
# uvicorn src.api.app:app --reload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(InvalidTokenError, jwt_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.include_router(auth.auth_router)
app.include_router(clientes.cliente_router)
app.include_router(produtos.produtos_router)
app.include_router(vendas.vendas_router)
app.include_router(estoque.estoque_router)


@app.get("/")
async def root():
    return {
        "message": "Sistema de Loja API",
        "version": "2.0.0",
        "docs": "/docs",
        "authentication": "JWT Bearer Token"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
