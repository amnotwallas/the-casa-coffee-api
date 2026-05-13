from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.logger import get_logger

# Importamos todos los modelos aquí para que SQLModel los detecte
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, CartDB
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo

logger = get_logger(__name__)

# Cambiamos la URL para usar el driver asyncpg si no está ya presente
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
#    echo=settings.DEBUG,
    future=True,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
)

async def init_db():
    """Inicializa las tablas en la base de datos de forma asíncrona."""
    try:
        async with engine.begin() as conn:
            # SQLModel.metadata.create_all requiere un engine síncrono usualmente,
            # pero con run_sync podemos ejecutarlo en el contexto async.
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Tablas de base de datos inicializadas exitosamente (Async).")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)

async def get_session():
    """Generador de sesiones asíncronas para inyección de dependencias."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
