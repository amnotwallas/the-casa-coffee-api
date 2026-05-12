from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from app.core.logger import get_logger

# Importamos todos los modelos aquí para que SQLModel los detecte
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, CartDB
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo

logger = get_logger(__name__)

# echo=settings.DEBUG permite ver los queries SQL en consola
engine = create_engine(
    settings.DATABASE_URL,
    #echo=settings.DEBUG
    )

def init_db():
    """Inicializa las tablas en la base de datos."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Tablas de base de datos inicializadas exitosamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)

def get_session():
    """Generador de sesiones para inyección de dependencias."""
    with Session(engine) as session:
        yield session
