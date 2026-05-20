from typing import List, Optional
from sqlmodel import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admin import AdminNotification

class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notifications(self, limit: int = 20) -> List[AdminNotification]:
        statement = select(AdminNotification).order_by(desc(AdminNotification.created_at)).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def mark_as_read(self, notification_id: str) -> Optional[AdminNotification]:
        notification = await self.session.get(AdminNotification, notification_id)
        if notification:
            notification.read = True
            self.session.add(notification)
            await self.session.commit()
            await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(self):
        statement = select(AdminNotification).where(AdminNotification.read == False)
        result = await self.session.execute(statement)
        notifications = result.scalars().all()
        for n in notifications:
            n.read = True
            self.session.add(n)
        await self.session.commit()

    async def create_notification(self, type: str, title: str, body: str) -> AdminNotification:
        notification = AdminNotification(type=type, title=title, body=body)
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
