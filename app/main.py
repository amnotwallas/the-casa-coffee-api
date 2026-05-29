import uuid
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routers import auth, user, chat, products, cart, orders, support, admin, media
from app.core.exceptions import AppException
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

# Configuración de CORS para permitir peticiones desde el Dashboard
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://coffe-dashboard-beta.vercel.app",
    "https://coffe-dashboard-git-main-walter-jahir-ambriz-reynas-projects.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Maneja excepciones personalizadas de la aplicación y las convierte en respuestas JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    """Genera un Trace ID único para cada petición y lo inyecta en los logs."""
    trace_id = str(uuid.uuid4())[:8]
    
    # Inyectar trace_id en el registro de logs
    import logging
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.trace_id = trace_id
        return record

    logging.setLogRecordFactory(record_factory)
    
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Determinar nivel de log basado en el status code
    status_code = response.status_code
    log_msg = f"Request {request.method} {request.url.path} - Status: {status_code} - Processed in {process_time:.2f}ms"
    
    if status_code >= 500:
        logger.error(log_msg)
    elif status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)
    
    response.headers["X-Trace-Id"] = trace_id
    return response

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
