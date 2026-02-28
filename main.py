from fastapi import FastAPI
from app.api.clients_router import router as clients_router
from app.repositories.database import init_db

app = FastAPI(
    title="Clients API",
    description="Microservicio para gestión de clientes con importación Excel y ABM en SQLite.",
    version="1.0.0",
)

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def on_startup():
    init_db()


# Registrar el router de clientes
app.include_router(clients_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Clients API is running"}
