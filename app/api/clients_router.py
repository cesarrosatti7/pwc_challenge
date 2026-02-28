from fastapi import APIRouter, HTTPException, UploadFile, File, status
from app.models.client import ClientCreate, ClientUpdate, ClientResponse, ImportResponse
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])
service = ClientService()


# ─── POST /clients/import ────────────────────────────────────────────────────

@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Importar clientes desde un archivo Excel",
)
async def import_clients(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un Excel (.xlsx o .xls)",
        )

    content = await file.read()

    try:
        result = service.import_from_excel(content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return result


# ─── GET /clients ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[ClientResponse],
    summary="Listar todos los clientes",
)
def list_clients():
    return service.get_all()


# ─── GET /clients/{id} ────────────────────────────────────────────────────────

@router.get(
    "/{customer_id}",
    response_model=ClientResponse,
    summary="Obtener un cliente por ID",
)
def get_client(customer_id: int):
    client = service.get_by_id(customer_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con id={customer_id} no encontrado",
        )
    return client


# ─── PUT /clients/{id} ────────────────────────────────────────────────────────

@router.put(
    "/{customer_id}",
    response_model=ClientResponse,
    summary="Actualizar un cliente",
)
def update_client(customer_id: int, data: ClientUpdate):
    updated = service.update(customer_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con id={customer_id} no encontrado",
        )
    return updated


# ─── DELETE /clients/{id} ─────────────────────────────────────────────────────

@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un cliente",
)
def delete_client(customer_id: int):
    deleted = service.delete(customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con id={customer_id} no encontrado",
        )
