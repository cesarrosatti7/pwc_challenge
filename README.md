
## Estructura

```
clients_api/
├── app/
│   ├── api/
│   │   └── clients_router.py    # Endpoints REST
│   ├── services/
│   │   └── client_service.py    # Lógica de negocio
│   ├── repositories/
│   │   ├── database.py          # Conexión y creación de BD
│   │   └── client_repository.py # Acceso a datos SQLite
│   └── models/
│       └── client.py            # Esquemas Pydantic
├── main.py                      # Punto de entrada FastAPI
├── requirements.txt
└── README.md
```

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd clients_api
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la API

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva (Swagger): `http://localhost:8000/docs`

### 5. Probar conexión a API

```cmd
curl http://localhost:8000/
```
### 6. Importar el excel a DB

```cmd
curl -X POST http://localhost:8000/clients/import -F "file=@clientes.xlsx"
```

### 7. Utilizar los endpoints de la API

```cmd
Trabajar con los endpoints, también se puede probar de cargar nuevamente la db para verificar el manejo de duplicados
```

---

## Endpoints

| Método | URL | Descripción |
|---|---|---|
| POST | `/clients/import` | Importar clientes desde Excel |
| GET | `/clients` | Listar todos los clientes |
| GET | `/clients/{id}` | Obtener cliente por ID |
| PUT | `/clients/{id}` | Actualizar cliente |
| DELETE | `/clients/{id}` | Eliminar cliente |

---

## Formato del archivo Excel

El archivo debe llamarse `clientes.xlsx` y contener una hoja llamada **`Clientes`** con estas columnas:

| Columna | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `customer_id` | Entero | Sí | Único |
| `name` | String | Sí | No vacío |
| `email` | String | Sí | Formato válido |
| `country` | String | Sí | — |
| `age` | Entero | No | ≥ 18 si se informa |

---

## Respuesta del endpoint de importación

```json
{
  "summary": {
    "total_records": 10,
    "inserted": 8,
    "errors": 2
  },
  "error_details": [
    {
      "customer_id": 5,
      "row_number": 6,
      "errors": ["email: value is not a valid email address"]
    }
  ]
}
```

---

## Notas de diseño

- **Separación de capas**: La API no contiene lógica de negocio; el service no contiene SQL; el repository no contiene validaciones.
- **Transacción en bloque**: Los registros válidos se insertan todos juntos en una sola transacción para garantizar consistencia.
- **Detección de duplicados doble**: Se verifican duplicados tanto dentro del archivo Excel como contra la base de datos existente.
