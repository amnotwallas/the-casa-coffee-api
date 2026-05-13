from typing import List, Optional
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.core.logger import get_logger

logger = get_logger(__name__)

class ProductRepository:
    """
    Data access layer for Product entities.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_products(
        self, 
        category: Optional[str] = None, 
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Retrieve a list of products with optional category and search filters.
        """
        statement = select(Product)
        
        if category:
            statement = statement.where(Product.categoria["id"].astext == category)
        
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(
                (Product.nombre.ilike(search_filter)) | 
                (Product.descripcion.ilike(search_filter))
            )
        
        statement = statement.offset(offset).limit(limit)
        
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_products(self, category: Optional[str] = None, search: Optional[str] = None) -> int:
        """
        Get the total count of products matching the provided filters.
        """
        statement = select(func.count()).select_from(Product)
        
        if category:
            statement = statement.where(Product.categoria["id"].astext == category)
        
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(
                (Product.nombre.ilike(search_filter)) | 
                (Product.descripcion.ilike(search_filter))
            )
            
        result = await self.session.execute(statement)
        return result.scalar()

    async def find_product_by_id(self, product_id: str) -> Optional[Product]:
        """
        Find a single product by its unique identifier.
        """
        return await self.session.get(Product, product_id)

    async def create_product(self, product_data: dict) -> Product:
        """
        Create and persist a new product record.
        """
        product = Product(**product_data)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_product(self, product_id: str, update_data: dict) -> Optional[Product]:
        """
        Update an existing product's details.
        """
        product = await self.find_product_by_id(product_id)
        if product:
            for key, value in update_data.items():
                setattr(product, key, value)
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        return None

    async def delete_product(self, product_id: str) -> bool:
        """
        Remove a product from the database.
        """
        product = await self.find_product_by_id(product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
            return True
        return False
