from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.v1.routers import auth, user, chat, products, cart, orders, support, admin, media
from app.core.logger import ServerLogger, get_logger
from app.core.config import settings
from app.core.database import init_db
from app.core.firebase import init_firebase

# Setup Logging
ServerLogger.setup(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(
    title=settings.APP_NAME,
    description="API robusta para la mejor cafetería  - The Casa Chill & Coffe",
    version=settings.VERSION
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(cart.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(support.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info(f"--- {settings.APP_NAME} v{settings.VERSION} iniciado correctamente ---")
    init_db() # Inicializa conexión con Supabase
    init_firebase() # Inicializa Firebase Admin
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY no detectada. Las funciones de IA estarán deshabilitadas.")

@app.get("/")
async def root():
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs",
        "version": settings.VERSION
    }
