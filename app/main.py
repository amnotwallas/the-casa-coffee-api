from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.v1.routers import auth, user, chat, products, cart, orders, support, admin, media
from app.core.logger import ServerLogger, get_logger
from app.core.config import settings
from app.core.database import init_db
from app.core.firebase import init_firebase

# Initialize structured logging
ServerLogger.setup(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Initialize rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    logger.info(f"--- Starting {settings.APP_NAME} v{settings.VERSION} ---")
    
    # Initialize database connection and schemas
    await init_db()
    
    # Initialize Firebase Admin SDK
    init_firebase()
    
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found. AI features will be disabled.")
    
    yield
    
    logger.info(f"--- Stopping {settings.APP_NAME} ---")

app = FastAPI(
    title=settings.APP_NAME,
    description="Professional backend API for The Casa Chill & Coffe coffee shop.",
    version=settings.VERSION,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(cart.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(support.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Health check and welcome endpoint.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "version": settings.VERSION
    }
