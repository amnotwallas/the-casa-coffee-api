from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[User]:
        statement = select(User)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def find_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_by_firebase_uid(self, uid: str) -> Optional[User]:
        statement = select(User).where(User.firebase_uid == uid)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_by_id(self, user_id: str) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def create(self, user_obj: User) -> User:
        self.session.add(user_obj)
        await self.session.commit()
        await self.session.refresh(user_obj)
        logger.info(f"Usuario creado en DB: {user_obj.email}")
        return user_obj

    async def update(self, user_id: str, update_data: dict) -> Optional[User]:
        user = await self.find_by_id(user_id)
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Usuario {user_id} actualizado en DB.")
            return user
        return None

    async def add_address(self, user_id: str, address_data: dict) -> dict:
        user = await self.find_by_id(user_id)
        if user:
            import uuid
            address_data["id"] = f"addr-{str(uuid.uuid4())[:8]}"
            new_dirs = list(user.direcciones)
            new_dirs.append(address_data)
            user.direcciones = new_dirs
            self.session.add(user)
            await self.session.commit()
            return address_data
        return {}

    async def delete_address(self, user_id: str, address_id: str) -> bool:
        user = await self.find_by_id(user_id)
        if user:
            original_len = len(user.direcciones)
            user.direcciones = [a for a in user.direcciones if a["id"] != address_id]
            if len(user.direcciones) < original_len:
                self.session.add(user)
                await self.session.commit()
                return True
        return False

    async def add_favorite(self, user_id: str, product_id: str):
        user = await self.find_by_id(user_id)
        if user:
            new_favs = list(user.favoritos)
            if product_id not in new_favs:
                new_favs.append(product_id)
                user.favoritos = new_favs
                self.session.add(user)
                await self.session.commit()

    async def remove_favorite(self, user_id: str, product_id: str):
        user = await self.find_by_id(user_id)
        if user:
            user.favoritos = [p for p in user.favoritos if p != product_id]
            self.session.add(user)
            await self.session.commit()
