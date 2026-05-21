from typing import List, Optional
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product, Category
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
        from sqlalchemy.orm import selectinload
        from app.models.product import Customization
        
        # Primero construir el query base
        statement = select(Product)
        
        if category:
            try:
                cat_int = int(category)
                statement = statement.where(Product.category_id == cat_int)
            except (ValueError, TypeError):
                pass
        
        if search:
            search_filter = f"%{search}%"
            starts_with_filter = f"{search}%"
            
            # Filtro de búsqueda
            statement = statement.where(
                (Product.nombre.ilike(search_filter)) | 
                (Product.descripcion.ilike(search_filter))
            )
            
            # Prioridad de ordenamiento:
            # 1. Empieza con el término en el nombre
            # 2. Contiene el término en el nombre
            # 3. Lo tiene en la descripción (por defecto si pasó el where)
            from sqlalchemy import case
            statement = statement.order_by(
                case(
                    (Product.nombre.ilike(starts_with_filter), 1),
                    (Product.nombre.ilike(search_filter), 2),
                    else_=3
                ).asc(),
                Product.rating_avg.desc() # Criterio secundario
            )
        
        statement = statement.offset(offset).limit(limit)
        
        # Eager loading de relaciones para evitar N+1
        statement = statement.options(
            selectinload(Product.categoria),
            selectinload(Product.valores_nutricionales),
            selectinload(Product.personalizaciones).selectinload(Customization.opciones)
        )
        
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_products(self, category: Optional[str] = None, search: Optional[str] = None) -> int:
        """
        Get the total count of products matching the provided filters.
        """
        statement = select(func.count()).select_from(Product)
        
        if category:
            try:
                cat_int = int(category)
                statement = statement.where(Product.category_id == cat_int)
            except (ValueError, TypeError):
                pass
        
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
        Find a single product by its unique identifier, including all details.
        """
        from sqlalchemy.orm import selectinload
        from app.models.product import Customization
        statement = select(Product).where(Product.id == product_id).options(
            selectinload(Product.categoria),
            selectinload(Product.valores_nutricionales),
            selectinload(Product.personalizaciones).selectinload(Customization.opciones)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_products_by_ids(self, product_ids: List[str]) -> List[Product]:
        """
        Fetch multiple products by their IDs in a single query.
        Useful to avoid N+1 query problems.
        """
        if not product_ids:
            return []
            
        statement = select(Product).where(Product.id.in_(product_ids))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_category_by_id(self, category_id: int) -> Optional[Category]:
        """
        Check if a category exists by its ID.
        """
        return await self.session.get(Category, category_id)

    async def create_product(self, product_data: dict) -> Product:
        """
        Create and persist a new product record with its related data.
        """
        from app.models.product import Nutrition, Customization, CustomizationOption
        
        # Extraer datos relacionales
        nutri_data = product_data.pop("valores_nutricionales", None)
        cust_list = product_data.pop("personalizaciones", [])
        
        # 1. Crear producto base
        product = Product(**product_data)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        
        # 2. Crear Nutrición
        if nutri_data:
            nutrition = Nutrition(product_id=product.id, **nutri_data)
            self.session.add(nutrition)
            
        # 3. Crear Personalizaciones
        for c in cust_list:
            opts = c.pop("opciones", [])
            cust = Customization(product_id=product.id, **c)
            self.session.add(cust)
            await self.session.flush()
            
            for o in opts:
                opt = CustomizationOption(customization_id=cust.id, **o)
                self.session.add(opt)
                
        await self.session.commit()
        # Cargar todo para devolver el objeto completo
        return await self.find_product_by_id(product.id)

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
