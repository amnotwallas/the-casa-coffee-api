from typing import List, Optional
from sqlmodel import Session, select
from app.models.product import Product
from app.core.logger import get_logger

logger = get_logger(__name__)

class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all_products(
        self, 
        category: Optional[str] = None, 
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Product]:
        statement = select(Product)
        
        # Filtrado por categoría (buscando dentro del JSON de categoria)
        if category:
            # PostgreSQL syntax para buscar en JSON: categoria->>'id' = 'category'
            # En SQLModel usamos .cast o comparaciones directas si es posible, 
            # pero dado que es un campo JSON, usaremos una aproximación compatible.
            statement = statement.where(Product.categoria["id"].astext == category)
        
        # Búsqueda por texto (nombre o descripción)
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(
                (Product.nombre.ilike(search_filter)) | 
                (Product.descripcion.ilike(search_filter))
            )
        
        # Paginación
        statement = statement.offset(offset).limit(limit)
        
        return self.session.exec(statement).all()

    def count_products(self, category: Optional[str] = None, search: Optional[str] = None) -> int:
        from sqlmodel import func
        statement = select(func.count()).select_from(Product)
        
        if category:
            statement = statement.where(Product.categoria["id"].astext == category)
        
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(
                (Product.nombre.ilike(search_filter)) | 
                (Product.descripcion.ilike(search_filter))
            )
            
        return self.session.exec(statement).one()

    def find_product_by_id(self, product_id: str) -> Optional[Product]:
        return self.session.get(Product, product_id)

    def create_product(self, product_data: dict) -> Product:
        product = Product(**product_data)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update_product(self, product_id: str, update_data: dict) -> Optional[Product]:
        product = self.find_product_by_id(product_id)
        if product:
            for key, value in update_data.items():
                setattr(product, key, value)
            self.session.add(product)
            self.session.commit()
            self.session.refresh(product)
            return product
        return None

    def delete_product(self, product_id: str) -> bool:
        product = self.find_product_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False
