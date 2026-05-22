from typing import List, Optional
from app.core.exceptions import BusinessLogicException, EntityNotFoundException
from app.repositories.support_repo import SupportRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.user_repo import UserRepository
from app.repositories.admin_repo import AdminRepository
from app.schemas.product_schema import Product as ProductSchema, ProductCreate
from app.schemas.order_schema import OrderBase

class AdminService:
    """
    Service layer for administrative operations and analytics.
    """
    def __init__(self, support_repo: SupportRepository, product_repo: ProductRepository, order_repo: OrderRepository, user_repo: UserRepository, admin_repo: AdminRepository):
        self.support_repo = support_repo
        self.product_repo = product_repo
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.admin_repo = admin_repo

    async def get_analytics(self) -> dict:
        """
        Gather system-wide analytics for the admin dashboard.
        Uses database-level aggregations for efficiency.
        """
        summary = await self.order_repo.get_analytics_summary()
        clientes = await self.user_repo.count_customers()
        productos = await self.product_repo.count_products()
        
        total_ventas = summary["total_ventas"]
        
        return {
            "ventasHoy": total_ventas,
            "ventasMes": summary["ventas_mes"],
            "pedidosPendientes": summary["pending_count"],
            "productosPopulares": summary["productos_populares"],
            "ingresos": summary.get("ingresos_desglosados", {"efectivo": 0.0, "tarjeta": 0.0}),
            "clientesTotales": clientes,
            "productosTotales": productos,
            "ventasSemanales": summary.get("ventas_semanales", []),
            "deltas": summary.get("deltas")
        }

    async def list_notifications(self, limit: int = 20) -> List[dict]:
        notifications = await self.admin_repo.get_notifications(limit)
        return [n.model_dump() for n in notifications]

    async def mark_notification_read(self, notification_id: str) -> dict:
        updated = await self.admin_repo.mark_as_read(notification_id)
        if not updated:
            raise EntityNotFoundException(message="Notification not found")
        return updated.model_dump()

    async def mark_all_notifications_read(self):
        await self.admin_repo.mark_all_as_read()
        return {"message": "Todas las notificaciones marcadas como leídas"}

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
        orders_data = await self.order_repo.list_all_orders()
        result = []
        for order, user in orders_data:
            customer_name = user.nombre if user else f"Usuario {order.user_id[:8]}"
            items_list = []
            for item in order.items:
                items_list.append({
                    "product_id": item.product_id,
                    "nombre": item.nombre,
                    "cantidad": item.cantidad,
                    "precio": item.precio,
                    "personalizaciones": item.personalizaciones,
                    "subtotal": item.subtotal
                })
                
            result.append({
                "id": order.id,
                "user_id": order.user_id,
                "customerName": customer_name,
                "fecha": order.fecha,
                "items": items_list,
                "total": order.total,
                "status": order.status,
                "tracking": order.tracking
            })
        return result

    async def update_order_status(self, order_id: str, status: str) -> dict:
        """
        Update order status and tracking information, and notify the user.
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

        # --- NOTIFICACIÓN AUTOMÁTICA AL CLIENTE ---
        status_messages = {
            "preparing": ("Estamos preparando tu pedido", "Tu café está en manos de nuestros baristas."),
            "ready": ("¡Tu pedido está listo!", "Ya puedes pasar por él o estar pendiente de la entrega."),
            "on_the_way": ("Tu pedido va en camino", "Nuestro repartidor está cerca de tu ubicación."),
            "delivered": ("Pedido entregado", "¡Gracias por elegir The Casa Chill & Coffee! Disfruta tu bebida."),
            "cancelled": ("Pedido cancelado", "Tu pedido ha sido cancelado. Si tienes dudas, contáctanos.")
        }

        if status in status_messages:
            titulo, mensaje = status_messages[status]
            from app.models.support import Notification
            
            notification = Notification(
                user_id=updated.user_id,
                titulo=titulo,
                mensaje=mensaje,
                tipo="ORDER_STATUS"
            )
            
            # Usamos el support_repo para guardar la notificación
            self.support_repo.session.add(notification)
            await self.support_repo.session.commit()

        return OrderBase.model_validate(updated).model_dump()
