from typing import List, Optional
from app.repositories.support_repo import SupportRepository
from app.schemas import support_schema as schema
from app.core.logger import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

class SupportService:
    def __init__(self, repository: SupportRepository):
        self.repository = repository

    # --- REVIEWS ---
    def get_product_reviews(self, product_id: str) -> schema.ProductReviewsResponse:
        reviews_models = self.repository.list_reviews_by_product(product_id)
        
        reviews_schemas = []
        for r in reviews_models:
            # Mapeamos de DB a Schema (notar cambio de user_id a userId, etc.)
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

    def add_product_review(self, product_id: str, user_id: str, user_name: str, review_in: schema.ReviewCreate) -> schema.Review:
        logger.info(f"Usuario {user_name} agregando reseña a producto {product_id}")
        review_data = {
            "user_id": user_id,
            "user_name": user_name,
            "rating": review_in.rating,
            "comentario": review_in.comentario,
            "fotos": review_in.fotos
        }
        
        r = self.repository.add_review(product_id, review_data)
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

    def mark_review_helpful(self, review_id: str) -> int:
        count = self.repository.mark_review_helpful(review_id)
        if count is None:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        return count

    # --- PROMOCIONES ---
    def get_active_promotions(self) -> List[schema.Promotion]:
        promos = self.repository.list_promotions()
        return [
            schema.Promotion(
                id=p.id,
                titulo=p.titulo,
                descripcion=p.descripcion,
                descuento=str(p.descuento), # Schema espera str para descuento? Revisar schema
                codigo=p.codigo,
                imagen=p.imagen
            ) for p in promos
        ]

    def get_promotion_by_id(self, promo_id: str) -> schema.Promotion:
        p = self.repository.find_promotion_by_id(promo_id)
        if not p:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        return schema.Promotion(
            id=p.id,
            titulo=p.titulo,
            descripcion=p.descripcion,
            descuento=str(p.descuento),
            codigo=p.codigo,
            imagen=p.imagen
        )

    # --- NOTIFICACIONES ---
    def get_user_notifications(self, user_id: str) -> List[schema.Notification]:
        notifs = self.repository.list_notifications(user_id)
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

    def mark_notification_read(self, user_id: str, notif_id: str):
        if not self.repository.mark_notification_read(user_id, notif_id):
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

    def mark_all_as_read(self, user_id: str):
        self.repository.mark_all_notifications_read(user_id)

    # --- INFO ---
    def get_store_hours(self) -> schema.StoreHours:
        info = self.repository.get_store_info()
        if not info:
             # Default mock si no hay nada en DB
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

    def get_full_store_info(self) -> dict:
        info = self.repository.get_store_info()
        return info.model_dump() if info else {}

    def get_faqs(self) -> List[schema.FAQ]:
        faqs = self.repository.get_faq()
        return [schema.FAQ(pregunta=f.pregunta, respuesta=f.respuesta, categoria=f.categoria) for f in faqs]

    def get_menu_of_day(self) -> dict:
        return self.repository.get_menu_of_day()

class AdminService:
    def __init__(self, support_repo: SupportRepository, product_repo: any, order_repo: any):
        self.support_repo = support_repo
        self.product_repo = product_repo
        self.order_repo = order_repo

    def get_analytics(self) -> dict:
        orders = self.order_repo.list_orders_by_user("admin") # Mock all orders
        total_ventas = sum(o.total for o in orders)
        
        return {
            "ventasHoy": total_ventas,
            "ventasMes": total_ventas * 1.2,
            "pedidosPendientes": len([o for o in orders if o.status == "pending"]),
            "productosPopulares": [{"nombre": "Frappé Mocha", "ventas": 15}],
            "ingresos": {"efectivo": total_ventas * 0.3, "tarjeta": total_ventas * 0.7}
        }

    def create_product(self, product_in: any) -> dict:
        product = self.product_repo.create_product(product_in.model_dump())
        return product.model_dump()

    def update_product(self, product_id: str, update_data: dict) -> dict:
        updated = self.product_repo.update_product(product_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return updated.model_dump()

    def delete_product(self, product_id: str):
        if not self.product_repo.delete_product(product_id):
            raise HTTPException(status_code=404, detail="Producto no encontrado")

    def list_all_orders(self) -> List[dict]:
        orders = self.order_repo.list_orders_by_user("admin")
        return [o.model_dump() for o in orders]

    def update_order_status(self, order_id: str, status: str) -> dict:
        tracking_map = {
            "preparing": {"preparando": True},
            "ready": {"listo": True},
            "on_the_way": {"enCamino": True},
            "delivered": {"entregado": True}
        }
        updated = self.order_repo.update_order_status(order_id, status, tracking_map.get(status))
        if not updated:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return updated.model_dump()
