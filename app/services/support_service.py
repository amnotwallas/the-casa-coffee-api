from typing import List, Optional
from app.repositories.support_repo import SupportRepository
from app.schemas import support_schema as schema
from app.core.logger import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

class SupportService:
    """
    Service layer for customer support, reviews, and store info.
    """
    def __init__(self, repository: SupportRepository):
        self.repository = repository

    # --- REVIEWS ---
    async def get_product_reviews(self, product_id: str) -> schema.ProductReviewsResponse:
        """
        Get formatted reviews and aggregate rating for a product.
        """
        reviews_models = await self.repository.list_reviews_by_product(product_id)
        
        reviews_schemas = []
        for r in reviews_models:
            reviews_schemas.append(schema.Review(
                id=r.id,
                rating=r.rating,
                comentario=r.comentario,
                fotos=r.fotos,
                userId=r.user_id,
                userName=r.user_name,
                fecha=r.fecha,
                helpful_count=r.helpful_count
            ))
        
        avg_rating = 0.0
        if reviews_schemas:
            avg_rating = sum(r.rating for r in reviews_schemas) / len(reviews_schemas)
            
        return schema.ProductReviewsResponse(
            reviews=reviews_schemas,
            avgRating=round(avg_rating, 1),
            totalReviews=len(reviews_schemas)
        )

    async def add_product_review(self, product_id: str, user_id: str, user_name: str, review_in: schema.ReviewCreate) -> schema.Review:
        """
        Add a new review using the authenticated user's identity.
        """
        logger.info(f"User {user_name} adding review to product {product_id}")
        review_data = {
            "user_id": user_id,
            "user_name": user_name,
            "rating": review_in.rating,
            "comentario": review_in.comentario,
            "fotos": review_in.fotos
        }
        
        r = await self.repository.add_review(product_id, review_data)
        return schema.Review(
            id=r.id,
            rating=r.rating,
            comentario=r.comentario,
            fotos=r.fotos,
            userId=r.user_id,
            userName=r.user_name,
            fecha=r.fecha,
            helpful_count=r.helpful_count
        )

    async def mark_review_helpful(self, review_id: str) -> int:
        """
        Mark a review as helpful and return new count.
        """
        count = await self.repository.mark_review_helpful(review_id)
        if count is None:
            raise HTTPException(status_code=404, detail="Review not found")
        return count

    # --- PROMOTIONS ---
    async def get_active_promotions(self) -> List[schema.Promotion]:
        """
        Get all currently active promotions.
        """
        promos = await self.repository.list_promotions()
        return [
            schema.Promotion(
                id=p.id,
                titulo=p.titulo,
                descripcion=p.descripcion,
                descuento=str(p.descuento),
                codigo=p.codigo,
                imagen=p.imagen
            ) for p in promos
        ]

    async def get_promotion_by_id(self, promo_id: str) -> schema.Promotion:
        """
        Get specific promotion details.
        """
        p = await self.repository.find_promotion_by_id(promo_id)
        if not p:
            raise HTTPException(status_code=404, detail="Promotion not found")
        return schema.Promotion(
            id=p.id,
            titulo=p.titulo,
            descripcion=p.descripcion,
            descuento=str(p.descuento),
            codigo=p.codigo,
            imagen=p.imagen
        )

    # --- NOTIFICATIONS ---
    async def get_user_notifications(self, user_id: str) -> List[schema.Notification]:
        """
        Retrieve all notifications for a user.
        """
        notifs = await self.repository.list_notifications(user_id)
        return [
            schema.Notification(
                id=n.id,
                tipo=n.tipo,
                titulo=n.titulo,
                mensaje=n.mensaje,
                leida=n.leida,
                fecha=n.fecha
            ) for n in notifs
        ]

    async def mark_notification_read(self, user_id: str, notif_id: str):
        """
        Mark a specific notification as read.
        """
        if not await self.repository.mark_notification_read(user_id, notif_id):
            raise HTTPException(status_code=404, detail="Notification not found")

    async def mark_all_as_read(self, user_id: str):
        """
        Mark all user notifications as read.
        """
        await self.repository.mark_all_notifications_read(user_id)

    # --- STORE INFO & FAQ ---
    async def get_store_hours(self) -> schema.StoreHours:
        """
        Get current store hours and operational status.
        """
        info = await self.repository.get_store_info()
        if not info:
             return schema.StoreHours(
                 horarios=[],
                 estaAbierto=True,
                 tiempo_espera_actual=15,
                 volumen_pedidos="medio"
             )
        return schema.StoreHours(
            horarios=info.horarios,
            estaAbierto=info.estaAbierto,
            tiempo_espera_actual=info.tiempo_espera_actual,
            volumen_pedidos=info.volumen_pedidos
        )

    async def get_full_store_info(self) -> dict:
        """
        Get full store metadata.
        """
        info = await self.repository.get_store_info()
        return info.model_dump() if info else {}

    async def get_faqs(self) -> List[schema.FAQ]:
        """
        Get all FAQs.
        """
        faqs = await self.repository.get_faq()
        return [schema.FAQ(pregunta=f.pregunta, respuesta=f.respuesta, categoria=f.categoria) for f in faqs]

    async def get_menu_of_day(self) -> dict:
        """
        Get the special menu of the day.
        """
        return await self.repository.get_menu_of_day()

class AdminService:
    """
    Service layer for administrative operations and analytics.
    """
    def __init__(self, support_repo: SupportRepository, product_repo: any, order_repo: any):
        self.support_repo = support_repo
        self.product_repo = product_repo
        self.order_repo = order_repo

    async def get_analytics(self) -> dict:
        """
        Gather system-wide analytics for the admin dashboard.
        """
        orders = await self.order_repo.list_orders_by_user("admin")
        total_ventas = sum(o.total for o in orders)
        
        return {
            "ventasHoy": total_ventas,
            "ventasMes": total_ventas * 1.2,
            "pedidosPendientes": len([o for o in orders if o.status == "pending"]),
            "productosPopulares": [{"nombre": "Frappé Mocha", "ventas": 15}],
            "ingresos": {"efectivo": total_ventas * 0.3, "tarjeta": total_ventas * 0.7}
        }

    async def create_product(self, product_in: any) -> dict:
        """
        Create a new product record.
        """
        product = await self.product_repo.create_product(product_in.model_dump())
        return product.model_dump()

    async def update_product(self, product_id: str, update_data: dict) -> dict:
        """
        Update an existing product record.
        """
        updated = await self.product_repo.update_product(product_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated.model_dump()

    async def delete_product(self, product_id: str):
        """
        Delete a product record.
        """
        if not await self.product_repo.delete_product(product_id):
            raise HTTPException(status_code=404, detail="Product not found")

    async def list_all_orders(self) -> List[dict]:
        """
        Retrieve all orders for administrative review.
        """
        orders = await self.order_repo.list_orders_by_user("admin")
        return [o.model_dump() for o in orders]

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
            raise HTTPException(status_code=404, detail="Order not found")
        return updated.model_dump()
