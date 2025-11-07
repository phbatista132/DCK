from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import clientes, produtos, vendas, estoque
app = FastAPI(title="API Sistema de Loja", description="API REST para gerenciamento de loja", version="1.0.0")
# uvicorn src.api.app:app --reload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.cliente_router)
app.include_router(produtos.produtos_router)
app.include_router(vendas.vendas_router)
app.include_router(estoque.estoque_router)


@app.get("/")
async def root():
    """Healt check"""
    return {
        "status": "Online",
        "message": "API Sistema de loja",
        "version": "1.0.0",
        "docs": "/docs"
            }