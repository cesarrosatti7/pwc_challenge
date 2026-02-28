import re
import io
from typing import Optional

import pandas as pd
from pydantic import ValidationError

from app.models.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ImportErrorDetail,
    ImportResponse,
    ImportSummary,
)
from app.repositories.client_repository import ClientRepository

# Columnas exactas que debe tener el Excel
REQUIRED_COLUMNS = {"customer_id", "name", "email", "country", "age"}

# Regex simple para validar email (además de Pydantic EmailStr)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ClientService:
    """
    Capa de lógica de negocio.
    Orquesta validaciones y delega persistencia al repository.
    """

    def __init__(self):
        self.repo = ClientRepository()

    # ─── ABM básico ───────────────────────────────────────────────────────────

    def get_all(self) -> list[ClientResponse]:
        return self.repo.get_all()

    def get_by_id(self, customer_id: int) -> Optional[ClientResponse]:
        return self.repo.get_by_id(customer_id)

    def create(self, client: ClientCreate) -> ClientResponse:
        if self.repo.exists(client.customer_id):
            raise ValueError(f"Ya existe un cliente con customer_id={client.customer_id}")
        return self.repo.insert(client)

    def update(self, customer_id: int, data: ClientUpdate) -> Optional[ClientResponse]:
        if not self.repo.exists(customer_id):
            return None
        return self.repo.update(customer_id, data)

    def delete(self, customer_id: int) -> bool:
        return self.repo.delete(customer_id)

    # ─── Importación Excel ────────────────────────────────────────────────────

    def import_from_excel(self, file_bytes: bytes) -> ImportResponse:
        """
        Proceso completo de importación:
        1. Parsear el Excel.
        2. Validar estructura (columnas).
        3. Validar cada fila.
        4. Detectar IDs duplicados dentro del archivo y en la BD.
        5. Insertar los válidos.
        6. Retornar resumen con errores.
        """
        # 1. Parsear Excel
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Clientes")
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel: {e}")

        # 2. Validar columnas exactas
        actual_columns = set(df.columns.str.strip().str.lower())
        if actual_columns != REQUIRED_COLUMNS:
            missing = REQUIRED_COLUMNS - actual_columns
            extra = actual_columns - REQUIRED_COLUMNS
            msg_parts = []
            if missing:
                msg_parts.append(f"Columnas faltantes: {missing}")
            if extra:
                msg_parts.append(f"Columnas no esperadas: {extra}")
            raise ValueError(". ".join(msg_parts))

        # Normalizar nombres de columna
        df.columns = df.columns.str.strip().str.lower()

        total = len(df)
        valid_clients: list[ClientCreate] = []
        error_details: list[ImportErrorDetail] = []

        # Rastrear IDs vistos dentro del mismo archivo (para detectar duplicados internos)
        seen_ids: set[int] = set()

        # Pre-consultar IDs que ya existen en la BD
        candidate_ids = [
            int(row["customer_id"])
            for _, row in df.iterrows()
            if pd.notna(row.get("customer_id"))
            and str(row["customer_id"]).strip() != ""
        ]
        existing_db_ids = self.repo.get_existing_ids(candidate_ids) if candidate_ids else set()

        # 3. Validar fila por fila
        for row_num, (_, row) in enumerate(df.iterrows(), start=2):  # start=2 porque fila 1 es header
            row_errors: list[str] = []

            # Extraer customer_id
            raw_id = row.get("customer_id")
            customer_id: Optional[int] = None

            if pd.isna(raw_id) or str(raw_id).strip() == "":
                row_errors.append("customer_id es obligatorio")
            else:
                try:
                    customer_id = int(raw_id)
                except (ValueError, TypeError):
                    row_errors.append("customer_id debe ser un entero")

            # Validar age antes de Pydantic para mensajes más claros
            raw_age = row.get("age")
            age: Optional[int] = None
            if pd.notna(raw_age) and str(raw_age).strip() != "":
                try:
                    age = int(raw_age)
                except (ValueError, TypeError):
                    row_errors.append("age debe ser un entero")

            # Duplicado interno en el archivo
            if customer_id is not None:
                if customer_id in seen_ids:
                    row_errors.append(f"customer_id={customer_id} está duplicado en el archivo")
                    customer_id = None  # no agregar a seen_ids otra vez
                elif customer_id in existing_db_ids:
                    row_errors.append(f"customer_id={customer_id} ya existe en la base de datos")
                else:
                    seen_ids.add(customer_id)

            # Validar con Pydantic (captura name, email, country, age)
            if not row_errors or customer_id is not None:
                try:
                    client = ClientCreate(
                        customer_id=customer_id or 0,
                        name=str(row.get("name", "") or "").strip(),
                        email=str(row.get("email", "") or "").strip(),
                        country=str(row.get("country", "") or "").strip(),
                        age=age,
                    )
                    if not row_errors:
                        valid_clients.append(client)
                except ValidationError as ve:
                    for err in ve.errors():
                        field = err.get("loc", ["?"])[0]
                        msg = err.get("msg", "Error de validación")
                        # Limpiar prefijo "Value error, " de Pydantic v2
                        msg = msg.replace("Value error, ", "")
                        row_errors.append(f"{field}: {msg}")

            if row_errors:
                error_details.append(
                    ImportErrorDetail(
                        customer_id=customer_id,
                        row_number=row_num,
                        errors=row_errors,
                    )
                )

        # 4. Insertar válidos en bloque
        inserted = 0
        if valid_clients:
            inserted = self.repo.insert_many(valid_clients)

        return ImportResponse(
            summary=ImportSummary(
                total_records=total,
                inserted=inserted,
                errors=len(error_details),
            ),
            error_details=error_details,
        )
