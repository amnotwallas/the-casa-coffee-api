from typing import List, Optional
from sqlmodel import Session, select
from app.models.product import Product
from app.core.logger import get_logger

logger = get_logger(__name__)

class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all_products(self) -> List[Product]:
        statement = select(Product)
        return self.session.exec(statement).all()

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
