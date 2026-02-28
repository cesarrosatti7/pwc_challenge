from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class ClientBase(BaseModel):
    """Campos comunes a crear y actualizar un cliente."""
    name: str
    email: EmailStr
    country: str
    age: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

    @field_validator("age")
    @classmethod
    def age_must_be_adult(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 18:
            raise ValueError("La edad debe ser mayor o igual a 18")
        return v


class ClientCreate(ClientBase):
    """Schema para crear un cliente (incluye customer_id)."""
    customer_id: int


class ClientUpdate(ClientBase):
    """Schema para actualizar un cliente (todos los campos son opcionales excepto los básicos)."""
    pass


class ClientResponse(ClientBase):
    """Schema de respuesta con todos los campos."""
    customer_id: int

    class Config:
        from_attributes = True


class ImportErrorDetail(BaseModel):
    customer_id: Optional[int] = None
    row_number: Optional[int] = None
    errors: list[str]


class ImportSummary(BaseModel):
    total_records: int
    inserted: int
    errors: int


class ImportResponse(BaseModel):
    summary: ImportSummary
    error_details: list[ImportErrorDetail]
