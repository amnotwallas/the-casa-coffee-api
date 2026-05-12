from typing import List, Optional
from sqlmodel import Session, select
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[User]:
        statement = select(User)
        return self.session.exec(statement).all()

    def find_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def find_by_firebase_uid(self, uid: str) -> Optional[User]:
        statement = select(User).where(User.firebase_uid == uid)
        return self.session.exec(statement).first()

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self.session.get(User, user_id)

    def create(self, user_obj: User) -> User:
        self.session.add(user_obj)
        self.session.commit()
        self.session.refresh(user_obj)
        logger.info(f"Usuario creado en DB: {user_obj.email}")
        return user_obj

    def update(self, user_id: str, update_data: dict) -> Optional[User]:
        user = self.find_by_id(user_id)
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            logger.info(f"Usuario {user_id} actualizado en DB.")
            return user
        return None

    def add_address(self, user_id: str, address_data: dict) -> dict:
        user = self.find_by_id(user_id)
        if user:
            # Importante: Como direcciones es JSON, necesitamos re-asignarlo 
            # para que SQLAlchemy detecte el cambio si es una lista mutable
            import uuid
            address_data["id"] = f"addr-{str(uuid.uuid4())[:8]}"
            new_dirs = list(user.direcciones)
            new_dirs.append(address_data)
            user.direcciones = new_dirs
            self.session.add(user)
            self.session.commit()
            return address_data
        return {}

    def delete_address(self, user_id: str, address_id: str) -> bool:
        user = self.find_by_id(user_id)
        if user:
            original_len = len(user.direcciones)
            user.direcciones = [a for a in user.direcciones if a["id"] != address_id]
            if len(user.direcciones) < original_len:
                self.session.add(user)
                self.session.commit()
                return True
        return False

    def add_favorite(self, user_id: str, product_id: str):
        user = self.find_by_id(user_id)
        if user:
            new_favs = list(user.favoritos)
            if product_id not in new_favs:
                new_favs.append(product_id)
                user.favoritos = new_favs
                self.session.add(user)
                self.session.commit()

    def remove_favorite(self, user_id: str, product_id: str):
        user = self.find_by_id(user_id)
        if user:
            user.favoritos = [p for p in user.favoritos if p != product_id]
            self.session.add(user)
            self.session.commit()
