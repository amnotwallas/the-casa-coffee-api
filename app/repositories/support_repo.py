from typing import List, Optional
from sqlmodel import Session, select
from app.models.support import Review, Promotion, Notification, FAQ, StoreInfo
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class SupportRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- REVIEWS ---
    def list_reviews_by_product(self, product_id: str) -> List[Review]:
        statement = select(Review).where(Review.product_id == product_id)
        return self.session.exec(statement).all()

    def add_review(self, product_id: str, review_data: dict) -> Review:
        review = Review(product_id=product_id, **review_data)
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def mark_review_helpful(self, review_id: str) -> Optional[int]:
        review = self.session.get(Review, review_id)
        if review:
            review.helpful_count += 1
            self.session.add(review)
            self.session.commit()
            self.session.refresh(review)
            return review.helpful_count
        return None

    # --- PROMOCIONES ---
    def list_promotions(self, active_only: bool = True) -> List[Promotion]:
        statement = select(Promotion)
        if active_only:
            statement = statement.where(Promotion.activo == True)
        return self.session.exec(statement).all()

    def find_promotion_by_id(self, promo_id: str) -> Optional[Promotion]:
        return self.session.get(Promotion, promo_id)

    # --- NOTIFICACIONES ---
    def list_notifications(self, user_id: str) -> List[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id).order_by(Notification.fecha.desc())
        return self.session.exec(statement).all()

    def mark_notification_read(self, user_id: str, notif_id: str) -> bool:
        statement = select(Notification).where(Notification.id == notif_id, Notification.user_id == user_id)
        notification = self.session.exec(statement).first()
        if notification:
            notification.leida = True
            self.session.add(notification)
            self.session.commit()
            return True
        return False

    def mark_all_notifications_read(self, user_id: str):
        statement = select(Notification).where(Notification.user_id == user_id, Notification.leida == False)
        notifications = self.session.exec(statement).all()
        for n in notifications:
            n.leida = True
            self.session.add(n)
        self.session.commit()

    # --- INFO ---
    def get_faq(self) -> List[FAQ]:
        statement = select(FAQ)
        return self.session.exec(statement).all()
    
    def get_store_info(self) -> Optional[StoreInfo]:
        # Suponemos que solo hay un registro de StoreInfo con id=1
        return self.session.get(StoreInfo, 1)

    def update_store_info(self, info_data: dict) -> StoreInfo:
        store_info = self.get_store_info()
        if not store_info:
            store_info = StoreInfo(id=1, **info_data)
        else:
            for key, value in info_data.items():
                setattr(store_info, key, value)
        
        self.session.add(store_info)
        self.session.commit()
        self.session.refresh(store_info)
        return store_info

    def get_menu_of_day(self) -> dict:
        # Por ahora lo mantenemos simple, podría ser otra tabla o un campo en StoreInfo
        return {"titulo": "Especial del Día", "productos": []}
