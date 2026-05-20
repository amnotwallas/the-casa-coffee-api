from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.logger import get_logger

# Import all models to ensure SQLModel detects them
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, CartDB
from app.models.admin import AdminNotification
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo

logger = get_logger(__name__)

# Ensure the database URL uses the asyncpg driver
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=False, # Set to True for SQL debugging
    future=True,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
)

async def init_db():
    """
    Initialize database tables asynchronously.
    """
    try:
        async with engine.begin() as conn:
            # SQLModel.metadata.create_all is a synchronous call; 
            # run_sync bridges it into the async context.
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)

async def get_session():
    """
    Dependency generator for asynchronous database sessions.
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
