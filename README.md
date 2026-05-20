# ☕ The Casa Chill & Coffee API

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLModel](https://img.shields.io/badge/SQLModel-0.0.22-009688?style=flat)](https://sqlmodel.tiangolo.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Admin_SDK-FFCA28?style=flat&logo=firebase&logoColor=white)](https://firebase.google.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=flat&logo=postgresql&logoColor=white)](https://supabase.com/)

API robusta, moderna y escalable diseñada para la gestión integral de una cafetería premium. Implementa una **Arquitectura en Capas (Layered Architecture)** para garantizar mantenibilidad, testabilidad y una clara separación de responsabilidades.

---

## 🚀 Características Principales

- **Inteligencia Artificial:** Integración con **Groq (Llama 3.1)** para un asistente de café inteligente y recomendaciones personalizadas.
- **Seguridad de Grado Industrial:** Autenticación delegada en **Firebase Admin SDK**. Sincronización automática de perfiles.
- **Persistencia Robusta:** Uso de **SQLModel** (Pydantic + SQLAlchemy) con **PostgreSQL** alojado en **Supabase**.
- **Gestión de Media:** Servidor de assets estáticos con generación dinámica de URLs para productos y promociones.
- **Rendimiento Optimizado:** Construido sobre **FastAPI** y gestionado con **uv** para una velocidad de desarrollo y ejecución superior.
- **Arquitectura Profesional:**
    - `Routers`: Definición de endpoints y validación de esquemas.
    - `Services`: Lógica de negocio pura.
    - `Repositories`: Abstracción del acceso a datos.
    - `Models`: Definiciones de tablas y tipos.

---

## 🛠️ Stack Tecnológico

- **Core:** FastAPI, Uvicorn, Pydantic (v2).
- **Database:** SQLModel, PostgreSQL (Supabase).
- **Auth:** Firebase Admin SDK.
- **AI:** Groq SDK.
- **Tooling:** `uv` (Package Manager), `Makefile`, `Python-Dotenv`.

---

## 📂 Estructura del Proyecto

```text
app/
├── ai/           # Agentes de IA y proveedores (Groq)
├── api/          # Routers (v1) y dependencias de seguridad
├── core/         # Configuración global, DB y Firebase init
├── data/         # Archivos estáticos e imágenes de productos
├── models/       # Modelos de base de datos (SQLModel)
├── repositories/ # Capa de persistencia (Queries SQL)
├── schemas/      # Modelos de validación Pydantic
└── services/     # Lógica de negocio (Orquestación)
```

---

## ⚙️ Instalación y Configuración

### Prerrequisitos
- [uv](https://github.com/astral-sh/uv) instalado.
- Cuenta en Supabase y Firebase.

### Pasos

1. **Clonar e Instalar:**
   ```bash
   make install
   ```

2. **Variables de Entorno:**
   Crea un archivo `.env` basado en `.env.example`:
   ```env
   DATABASE_URL="postgresql://user:pass@host:6543/postgres"
   FIREBASE_CREDENTIALS="path/to/firebase-sdk.json"
   GROQ_API_KEY="gsk_..."
   BASE_URL="http://localhost:8000"
   ```

3. **Poblar Base de Datos (Opcional):**
   ```bash
   make seed
   ```

4. **Ejecutar en Desarrollo:**
   ```bash
   make dev
   ```

---

## 🔌 API Endpoints (Resumen)

La API está documentada interactivamente en `/docs` (Swagger) o `/redoc`.

- **`Auth`**: `/api/v1/auth/verify` - Sincronización con Firebase.
- **`User`**: `/api/v1/user/profile`, `/addresses`, `/favorites`.
- **`Products`**: `/api/v1/products` - Catálogo completo con imágenes.
- **`Cart`**: `/api/v1/cart` - Gestión de carrito persistente.
- **`Orders`**: `/api/v1/orders` - Creación y seguimiento de pedidos.
- **`Support/AI`**: `/api/v1/support/chat` - Asistente inteligente.

---

## 🛠️ Comandos Útiles (Makefile)

| Comando | Descripción |
| :--- | :--- |
| `make install` | Instala dependencias y sincroniza el entorno con `uv`. |
| `make dev` | Inicia el servidor FastAPI con hot-reload. |
| `make seed` | Ejecuta el script de carga de datos iniciales. |
| `make export` | Genera `requirements.txt` actualizado. |
| `make clean` | Limpia caches y el entorno virtual. |

## ⚡ Rendimiento y Optimización

La API ha sido optimizada para ofrecer tiempos de respuesta sub-segundo incluso bajo carga:

- **Consultas Paralelas:** Uso de ejecución asíncrona para métricas de Dashboard, reduciendo la latencia de segundos a milisegundos.
- **Resolución de N+1:** Implementación de carga masiva de productos en el checkout, evitando múltiples llamadas a la base de datos por un solo pedido.
- **Indexación Estratégica:** Columnas de alto tráfico (`fecha`, `status`) indexadas en PostgreSQL para búsquedas instantáneas.
- **Arquitectura Eficiente:** Gestión de dependencias con `uv` y ejecución sobre `FastAPI` asíncrono.

---

## 🧪 Pruebas y Colecciones

Se incluyen colecciones de **Postman** en la raíz para facilitar las pruebas:
- `coffee_api_client.json`: Flujos completos para el cliente.
- `coffee_api_admin.json`: Endpoints administrativos.

---
Desarrollado con mucho cafe para **The Casa Chill & Coffee**.
