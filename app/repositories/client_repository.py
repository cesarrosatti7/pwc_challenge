import sqlite3
from typing import Optional
from app.repositories.database import get_connection
from app.models.client import ClientCreate, ClientUpdate, ClientResponse


class ClientRepository:
    """
    Capa de acceso a datos.
    Solo interactúa con SQLite, no contiene lógica de negocio.
    """

    def get_all(self) -> list[ClientResponse]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM clients").fetchall()
        return [ClientResponse(**dict(row)) for row in rows]

    def get_by_id(self, customer_id: int) -> Optional[ClientResponse]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE customer_id = ?", (customer_id,)
            ).fetchone()
        return ClientResponse(**dict(row)) if row else None

    def exists(self, customer_id: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM clients WHERE customer_id = ?", (customer_id,)
            ).fetchone()
        return row is not None

    def insert(self, client: ClientCreate) -> ClientResponse:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO clients (customer_id, name, email, country, age)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client.customer_id, client.name, client.email, client.country, client.age),
            )
            conn.commit()
        return self.get_by_id(client.customer_id)

    def insert_many(self, clients: list[ClientCreate]) -> int:
        """Inserta múltiples clientes en una sola transacción. Retorna cantidad insertada."""
        data = [
            (c.customer_id, c.name, c.email, c.country, c.age)
            for c in clients
        ]
        with get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO clients (customer_id, name, email, country, age)
                VALUES (?, ?, ?, ?, ?)
                """,
                data,
            )
            conn.commit()
        return len(data)

    def update(self, customer_id: int, data: ClientUpdate) -> Optional[ClientResponse]:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE clients
                SET name = ?, email = ?, country = ?, age = ?
                WHERE customer_id = ?
                """,
                (data.name, data.email, data.country, data.age, customer_id),
            )
            conn.commit()
        return self.get_by_id(customer_id)

    def delete(self, customer_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM clients WHERE customer_id = ?", (customer_id,)
            )
            conn.commit()
        return cursor.rowcount > 0

    def get_existing_ids(self, ids: list[int]) -> set[int]:
        """Devuelve el subconjunto de IDs que ya existen en la base."""
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT customer_id FROM clients WHERE customer_id IN ({placeholders})", ids
            ).fetchall()
        return {row["customer_id"] for row in rows}
