from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class SupportRepository:
    """
    Data access layer for Support-related entities (Reviews, Promos, Notifications).
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- REVIEWS ---
    async def list_reviews_by_product(self, product_id: str) -> List[Review]:
        """
        Retrieve all reviews for a specific product.
        """
        statement = select(Review).where(Review.product_id == product_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add_review(self, product_id: str, review_data: dict) -> Review:
        """
        Persist a new product review.
        """
        review = Review(product_id=product_id, **review_data)
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def mark_review_helpful(self, review_id: str) -> Optional[int]:
        """
        Increment the helpful counter for a review.
        """
        review = await self.session.get(Review, review_id)
        if review:
            review.helpful_count += 1
            self.session.add(review)
            await self.session.commit()
            await self.session.refresh(review)
            return review.helpful_count
        return None

    # --- PROMOTIONS ---
    async def list_promotions(self, active_only: bool = True) -> List[Promotion]:
        """
        Retrieve available promotions.
        """
        statement = select(Promotion)
        if active_only:
            statement = statement.where(Promotion.activo == True)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def find_promotion_by_id(self, promo_id: str) -> Optional[Promotion]:
        """
        Find a promotion by its ID.
        """
        return await self.session.get(Promotion, promo_id)

    # --- NOTIFICATIONS ---
    async def list_notifications(self, user_id: str) -> List[Notification]:
        """
        Get all notifications for a specific user, ordered by newest.
        """
        statement = select(Notification).where(Notification.user_id == user_id).order_by(Notification.fecha.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def mark_notification_read(self, user_id: str, notif_id: str) -> bool:
        """
        Mark a single notification as read.
        """
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
        """
        Mark all unread notifications for a user as read.
        """
        statement = select(Notification).where(Notification.user_id == user_id, Notification.leida == False)
        result = await self.session.execute(statement)
        notifications = result.scalars().all()
        for n in notifications:
            n.leida = True
            self.session.add(n)
        await self.session.commit()

    # --- STORE INFO & FAQ ---
    async def get_faq(self) -> List[FAQ]:
        """
        Retrieve all FAQ items.
        """
        statement = select(FAQ)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def get_store_info(self) -> Optional[StoreInfo]:
        """
        Retrieve store-wide settings and information, including hours.
        """
        from sqlalchemy.orm import selectinload
        statement = select(StoreInfo).where(StoreInfo.id == 1).options(selectinload(StoreInfo.horarios))
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def update_store_info(self, info_data: dict) -> StoreInfo:
        """
        Update global store information.
        """
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
        """
        Retrieve the special menu or product of the day.
        """
        return {"title": "Daily Special", "products": []}
