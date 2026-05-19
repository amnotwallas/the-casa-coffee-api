from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

class UserRepository:
    """
    Data access layer for User entities and profile management.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[User]:
        """
        Retrieve all users registered in the system.
        """
        statement = select(User)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Locate a user by their email address.
        """
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_by_firebase_uid(self, uid: str) -> Optional[User]:
        """
        Locate a user by their Firebase Unique Identifier, including relationships.
        """
        from sqlalchemy.orm import selectinload
        statement = select(User).where(User.firebase_uid == uid).options(
            selectinload(User.direcciones),
            selectinload(User.favoritos),
            selectinload(User.preferencias)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their internal database ID, including their addresses and favorites.
        """
        from sqlalchemy.orm import selectinload
        statement = select(User).where(User.id == user_id).options(
            selectinload(User.direcciones),
            selectinload(User.favoritos),
            selectinload(User.preferencias)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create(self, user_obj: User) -> User:
        """
        Persist a new user in the database.
        """
        self.session.add(user_obj)
        await self.session.commit()
        await self.session.refresh(user_obj)
        
        # Inicializar preferencias por defecto
        from app.models.user import Preference
        pref = Preference(user_id=user_obj.id)
        self.session.add(pref)
        await self.session.commit()
        
        logger.info(f"User created in database: {user_obj.email}")
        return user_obj

    async def update(self, user_id: str, update_data: dict) -> Optional[User]:
        """
        Update user profile information and ensure relationships are loaded.
        """
        user = await self.session.get(User, user_id)
        if user:
            # Separar preferencias de datos de usuario
            pref_data = update_data.pop("preferencias", None)
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.session.add(user)
            
            if pref_data:
                # Recargar preferencias si existen
                from sqlalchemy.orm import selectinload
                statement = select(User).where(User.id == user_id).options(selectinload(User.preferencias))
                result = await self.session.execute(statement)
                user_with_pref = result.scalars().first()
                
                if user_with_pref and user_with_pref.preferencias:
                    for k, v in pref_data.items():
                        if hasattr(user_with_pref.preferencias, k):
                            setattr(user_with_pref.preferencias, k, v)
                    self.session.add(user_with_pref.preferencias)

            await self.session.commit()
            
            # Recargar con todas las relaciones
            from sqlalchemy.orm import selectinload
            statement = select(User).where(User.id == user_id).options(
                selectinload(User.direcciones),
                selectinload(User.favoritos),
                selectinload(User.preferencias)
            )
            result = await self.session.execute(statement)
            return result.scalars().first()
        return None

    async def add_address(self, user_id: str, address_data: dict) -> dict:
        """
        Add a new shipping address to the user's profile using the Address table.
        """
        from app.models.user import Address
        address = Address(user_id=user_id, **address_data)
        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return {
            "id": address.id,
            "calle": address.calle,
            "ciudad": address.ciudad,
            "codigoPostal": address.codigoPostal,
            "referencia": address.referencia,
            "esDefault": address.esDefault
        }

    async def delete_address(self, user_id: str, address_id: str) -> bool:
        """
        Remove a shipping address from the user's profile.
        """
        from app.models.user import Address
        statement = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        result = await self.session.execute(statement)
        address = result.scalars().first()
        if address:
            await self.session.delete(address)
            await self.session.commit()
            return True
        return False

    async def add_favorite(self, user_id: str, product_id: str):
        """
        Add a product to the user's favorites list using the linking table directly.
        """
        from app.models.product import UserFavorite
        # Verificar si ya existe para evitar duplicados
        stmt = select(UserFavorite).where(
            UserFavorite.user_id == user_id, 
            UserFavorite.product_id == product_id
        )
        result = await self.session.execute(stmt)
        if not result.scalars().first():
            self.session.add(UserFavorite(user_id=user_id, product_id=product_id))
            await self.session.commit()

    async def remove_favorite(self, user_id: str, product_id: str):
        """
        Remove a product from the user's favorites list using the linking table.
        """
        from app.models.product import UserFavorite
        from sqlalchemy import delete
        stmt = delete(UserFavorite).where(
            UserFavorite.user_id == user_id, 
            UserFavorite.product_id == product_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_favorite_ids(self, user_id: str) -> List[str]:
        """
        Retrieve only the product IDs in the user's favorites list.
        Efficient alternative to loading the full User object.
        """
        from app.models.product import UserFavorite
        stmt = select(UserFavorite.product_id).where(UserFavorite.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
