from typing import List, Optional
from app.core.exceptions import BusinessLogicException, EntityNotFoundException
from app.repositories.support_repo import SupportRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.product_schema import Product as ProductSchema, ProductCreate
from app.schemas.order_schema import OrderBase

class AdminService:
    """
    Service layer for administrative operations and analytics.
    """
    def __init__(self, support_repo: SupportRepository, product_repo: ProductRepository, order_repo: OrderRepository):
        self.support_repo = support_repo
        self.product_repo = product_repo
        self.order_repo = order_repo

    async def get_analytics(self) -> dict:
        """
        Gather system-wide analytics for the admin dashboard.
        Uses database-level aggregations for efficiency.
        """
        summary = await self.order_repo.get_analytics_summary()
        total_ventas = summary["total_ventas"]
        
        return {
            "ventasHoy": total_ventas,
            "ventasMes": total_ventas * 1.2, # TODO: Implementar lógica real por fechas
            "pedidosPendientes": summary["pending_count"],
            "productosPopulares": [{"nombre": "Frappé Mocha", "ventas": 15}],
            "ingresos": {"efectivo": total_ventas * 0.3, "tarjeta": total_ventas * 0.7}
        }

    async def create_product(self, product_in: ProductCreate) -> dict:
        """
        Create a new product record using ProductCreate schema.
        Validates that the category exists before creation.
        """
        # Validar categoría
        category = await self.product_repo.find_category_by_id(product_in.category_id)
        if not category:
            raise BusinessLogicException(
                message=f"La categoría con ID {product_in.category_id} no existe. Cree la categoría antes de asignar productos."
            )
            
        product = await self.product_repo.create_product(product_in.model_dump())
        return ProductSchema.model_validate(product).model_dump()

    async def update_product(self, product_id: str, update_data: dict) -> dict:
        """
        Update an existing product record.
        Validates category_id if it's being updated.
        """
        # Si se intenta actualizar la categoría, validar que exista
        cat_id = update_data.get("category_id")
        if cat_id is not None:
            category = await self.product_repo.find_category_by_id(cat_id)
            if not category:
                raise BusinessLogicException(message=f"La categoría con ID {cat_id} no existe.")

        updated = await self.product_repo.update_product(product_id, update_data)
        if not updated:
            raise EntityNotFoundException(message="Product not found")
        return ProductSchema.model_validate(updated).model_dump()

    async def delete_product(self, product_id: str):
        """
        Delete a product record.
        """
        if not await self.product_repo.delete_product(product_id):
            raise EntityNotFoundException(message="Product not found")

    async def list_all_orders(self) -> List[dict]:
        """
        Retrieve all orders for administrative review.
        """
        orders = await self.order_repo.list_all_orders()
        return [OrderBase.model_validate(o).model_dump() for o in orders]

    async def update_order_status(self, order_id: str, status: str) -> dict:
        """
        Update order status and tracking information.
        """
        tracking_map = {
            "preparing": {"preparando": True},
            "ready": {"listo": True},
            "on_the_way": {"enCamino": True},
            "delivered": {"entregado": True}
        }
        updated = await self.order_repo.update_order_status(order_id, status, tracking_map.get(status))
        if not updated:
            raise EntityNotFoundException(message="Order not found")
        return OrderBase.model_validate(updated).model_dump()
