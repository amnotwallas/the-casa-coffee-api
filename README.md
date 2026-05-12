# The Casa Chill & Coffe API ☕️

API robusta y profesional para la mejor cafetería. Construida con **FastAPI** y diseñada siguiendo una arquitectura por capas (Layered Architecture), integrada con **Supabase (PostgreSQL)** y **Firebase**.

## 🚀 Características

- **Arquitectura Modular:** Separación estricta de responsabilidades (API, Services, Repositories, AI).
- **Persistencia en la Nube:** Integración completa con PostgreSQL (Supabase) mediante **SQLModel**.
- **Autenticación con Firebase:** Validación de identidad mediante tokens de Firebase Admin SDK.
- **Asistente de IA:** Integración con Groq (Llama 3.1) para recomendaciones personalizadas.
- **Manejo de Media:** Router dedicado para servir imágenes locales con generación dinámica de URLs.
- **Observabilidad:** Sistema de logueo estructurado con colores y niveles.
- **Gestión Moderna:** Automatización avanzada con `uv` y `Makefile`.

## 🛠️ Instalación y Uso

Asegúrate de tener [uv](https://github.com/astral-sh/uv) instalado.

1. **Instalar dependencias:**

   ```bash
   make install
   ```

2. **Configurar variables de entorno:**
   Crea un archivo `.env` basado en `.env.example` con las siguientes claves críticas:
   - `DATABASE_URL`: URL de conexión de Supabase (usar puerto 6543 para IPv4).
   - `FIREBASE_CREDENTIALS`: Ruta al archivo JSON de tu service account de Firebase.
   - `BASE_URL`: URL raíz del API (ej: `http://localhost:8000`).
   - `GROQ_API_KEY`: Tu llave de Groq para funciones de IA.

3. **Poblar la base de datos:**
   Ejecuta el script de carga inicial para crear las tablas y subir los productos:

   ```bash
   make seed
   ```

4. **Ejecutar servidor de desarrollo:**
   ```bash
   make dev
   ```

## 📁 Estructura del Proyecto

- `app/api/`: Capa de presentación (Routers y Dependencias).
- `app/services/`: Lógica de negocio y servicios core.
- `app/repositories/`: Acceso a datos (PostgreSQL/SQLModel).
- `app/models/`: Definición de tablas de base de datos.
- `app/ai/`: Integración con LLMs y Agentes.
- `app/core/`: Configuraciones globales, Firebase y DB.
- `app/data/static/`: Almacenamiento local de imágenes.

## 🔒 Autenticación

El backend no almacena contraseñas. El flujo es:

1. El cliente (iOS/Web) se autentica en Firebase.
2. El cliente envía el `id_token` al endpoint `POST /api/v1/auth/verify`.
3. El API valida el token y sincroniza el perfil del usuario en PostgreSQL.

## 🧪 Pruebas

Para ejecutar los tests unitarios:

```bash
make test
```

---

Desarrollado para el proyecto The Casa Chill & Coffe.
