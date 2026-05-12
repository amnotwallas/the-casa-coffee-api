from typing import List, Optional
from app.repositories.product_repo import ProductRepository
from app.schemas.product_schema import Product as ProductSchema

class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def get_all_products(self, category: Optional[str] = None, search: Optional[str] = None) -> List[ProductSchema]:
        db_products = self.repository.list_all_products()
        
        results = db_products
        if category:
            results = [p for p in results if p.categoria.get("id") == category]
        
        if search:
            search = search.lower()
            results = [p for p in results if search in p.nombre.lower() or search in p.descripcion.lower()]
            
        return [ProductSchema(**p.model_dump()) for p in results]

    def get_product_by_id(self, product_id: str) -> Optional[ProductSchema]:
        product = self.repository.find_product_by_id(product_id)
        return ProductSchema(**product.model_dump()) if product else None

    def get_categories(self) -> List[dict]:
        products = self.repository.list_all_products()
        cats = {}
        for p in products:
            c = p.categoria
            if c:
                cats[c.get("id")] = c
        return list(cats.values())

    def get_featured_products(self) -> List[ProductSchema]:
        products = self.repository.list_all_products()
        featured = [p for p in products if p.rating_avg >= 4.8]
        return [ProductSchema(**p.model_dump()) for p in featured]
