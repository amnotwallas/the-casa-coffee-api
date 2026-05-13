from typing import List, Optional
from app.repositories.product_repo import ProductRepository
from app.schemas.product_schema import Product as ProductSchema

class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def get_all_products(
        self, 
        category: Optional[str] = None, 
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> List[ProductSchema]:
        offset = (page - 1) * limit
        db_products = await self.repository.list_all_products(
            category=category, 
            search=search, 
            offset=offset, 
            limit=limit
        )
        return [ProductSchema(**p.model_dump()) for p in db_products]

    async def get_total_count(self, category: Optional[str] = None, search: Optional[str] = None) -> int:
        return await self.repository.count_products(category=category, search=search)

    async def get_product_by_id(self, product_id: str) -> Optional[ProductSchema]:
        product = await self.repository.find_product_by_id(product_id)
        return ProductSchema(**product.model_dump()) if product else None

    async def get_categories(self) -> List[dict]:
        products = await self.repository.list_all_products(limit=1000)
        cats = {}
        for p in products:
            c = p.categoria
            if c:
                cats[c.get("id")] = c
        return list(cats.values())

    async def get_featured_products(self) -> List[ProductSchema]:
        products = await self.repository.list_all_products(limit=100)
        featured = [p for p in products if p.rating_avg >= 4.8]
        return [ProductSchema(**p.model_dump()) for p in featured]
