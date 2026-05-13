from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class SupportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- REVIEWS ---
    async def list_reviews_by_product(self, product_id: str) -> List[Review]:
        statement = select(Review).where(Review.product_id == product_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add_review(self, product_id: str, review_data: dict) -> Review:
        review = Review(product_id=product_id, **review_data)
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def mark_review_helpful(self, review_id: str) -> Optional[int]:
        review = await self.session.get(Review, review_id)
        if review:
            review.helpful_count += 1
            self.session.add(review)
            await self.session.commit()
            await self.session.refresh(review)
            return review.helpful_count
        return None

    # --- PROMOCIONES ---
    async def list_promotions(self, active_only: bool = True) -> List[Promotion]:
        statement = select(Promotion)
        if active_only:
            statement = statement.where(Promotion.activo == True)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def find_promotion_by_id(self, promo_id: str) -> Optional[Promotion]:
        return await self.session.get(Promotion, promo_id)

    # --- NOTIFICACIONES ---
    async def list_notifications(self, user_id: str) -> List[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id).order_by(Notification.fecha.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def mark_notification_read(self, user_id: str, notif_id: str) -> bool:
        statement = select(Notification).where(Notification.id == notif_id, Notification.user_id == user_id)
        result = await self.session.execute(statement)
        notification = result.scalars().first()
        if notification:
            notification.leida = True
            self.session.add(notification)
            await self.session.commit()
            return True
        return False

    async def mark_all_notifications_read(self, user_id: str):
        statement = select(Notification).where(Notification.user_id == user_id, Notification.leida == False)
        result = await self.session.execute(statement)
        notifications = result.scalars().all()
        for n in notifications:
            n.leida = True
            self.session.add(n)
        await self.session.commit()

    # --- INFO ---
    async def get_faq(self) -> List[FAQ]:
        statement = select(FAQ)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def get_store_info(self) -> Optional[StoreInfo]:
        return await self.session.get(StoreInfo, 1)

    async def update_store_info(self, info_data: dict) -> StoreInfo:
        store_info = await self.get_store_info()
        if not store_info:
            store_info = StoreInfo(id=1, **info_data)
        else:
            for key, value in info_data.items():
                setattr(store_info, key, value)
        
        self.session.add(store_info)
        await self.session.commit()
        await self.session.refresh(store_info)
        return store_info

    async def get_menu_of_day(self) -> dict:
        return {"titulo": "Especial del Día", "productos": []}
