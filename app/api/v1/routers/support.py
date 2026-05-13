from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.support_schema import Promotion, Notification, FAQ, StoreHours
from app.services.support_service import SupportService
from app.api.dependencies import get_support_service, get_current_user_required
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Support"])

@router.get("/promotions", response_model=List[Promotion])
async def list_promotions(support_service: SupportService = Depends(get_support_service)):
    """Lista todas las promociones activas."""
    return await support_service.get_active_promotions()

@router.get("/promotions/{promo_id}", response_model=Promotion)
async def get_promotion(promo_id: str, support_service: SupportService = Depends(get_support_service)):
    """Detalle de una promoción específica."""
    return await support_service.get_promotion_by_id(promo_id)

@router.post("/coupons/validate")
async def validate_coupon(code: str):
    """Valida un código de cupón."""
    if code.upper() == "COFFEE10":
        return {"valido": True, "descuento": 0.10, "mensaje": "Cupón de 10% aplicado"}
    raise HTTPException(status_code=404, detail="Cupón inválido o expirado")

@router.get("/notifications", response_model=List[Notification])
async def list_notifications(
    support_service: SupportService = Depends(get_support_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Obtiene las notificaciones del usuario actual. REQUIERE LOGIN."""
    return await support_service.get_user_notifications(current_user["id"])

@router.patch("/notifications/{notif_id}/read")
async def mark_read(
    notif_id: str,
    support_service: SupportService = Depends(get_support_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Marca una notificación como leída. REQUIERE LOGIN."""
    await support_service.mark_notification_read(current_user["id"], notif_id)
    return {"message": "Notificación marcada como leída"}

@router.patch("/notifications/read-all")
async def mark_all_read(
    support_service: SupportService = Depends(get_support_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Marca todas las notificaciones como leídas. REQUIERE LOGIN."""
    await support_service.mark_all_as_read(current_user["id"])
    return {"message": "Todas las notificaciones marcadas como leídas"}

@router.get("/store/info")
async def get_store_info(support_service: SupportService = Depends(get_support_service)):
    """Obtiene información detallada de la tienda."""
    return await support_service.get_full_store_info()

@router.get("/store/hours", response_model=StoreHours)
async def get_store_hours(support_service: SupportService = Depends(get_support_service)):
    """Obtiene horarios y estado de disponibilidad de la tienda."""
    return await support_service.get_store_hours()

@router.get("/menu-of-day")
async def get_menu_of_day(support_service: SupportService = Depends(get_support_service)):
    """Obtiene el menú o especial del día."""
    return await support_service.get_menu_of_day()

@router.get("/faq", response_model=List[FAQ])
async def list_faqs(support_service: SupportService = Depends(get_support_service)):
    """Lista las preguntas frecuentes."""
    return await support_service.get_faqs()

@router.post("/notifications/token")
async def register_token(
    deviceToken: str,
    platform: str = "ios",
    current_user: dict = Depends(get_current_user_required)
):
    """Registra el token de dispositivo para Push Notifications. REQUIERE LOGIN."""
    logger.info(f"Token registrado para usuario {current_user['id']} en {platform}: {deviceToken[:10]}...")
    return {"message": "Token registrado correctamente"}

@router.patch("/reviews/{review_id}/helpful")
async def mark_helpful(
    review_id: str,
    support_service: SupportService = Depends(get_support_service)
):
    """Marca una reseña como útil."""
    new_count = await support_service.mark_review_helpful(review_id)
    return {"helpful_count": new_count}
