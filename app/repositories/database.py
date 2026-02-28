import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "clients.db"


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión a SQLite con row_factory para obtener dicts."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conn


def init_db() -> None:
    """Crea la tabla clients si no existe."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                customer_id INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                email       TEXT    NOT NULL,
                country     TEXT    NOT NULL,
                age         INTEGER
            )
        """)
        conn.commit()
