from typing import Optional, List
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.schemas.user_schema import FirebaseAuthRequest, AuthResponse, UserProfile
from app.core.logger import get_logger
from app.core.firebase import verify_firebase_token
from fastapi import HTTPException

logger = get_logger(__name__)

class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def verify_and_sync_user(self, auth_data: FirebaseAuthRequest) -> AuthResponse:
        """Verifica el token de Firebase y sincroniza el perfil local en Postgres."""
        logger.info("Iniciando verificación de token de Firebase")
        
        # 1. Validar Token con Firebase Admin
        decoded_token = verify_firebase_token(auth_data.firebase_token)
        if not decoded_token:
            logger.warning("Token de Firebase inválido o expirado")
            raise HTTPException(status_code=401, detail="Token de Firebase inválido")
        
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        nombre_firebase = decoded_token.get("name")
        foto_firebase = decoded_token.get("picture")

        # 2. Buscar usuario en Postgres por firebase_uid
        user = await self.repository.find_by_firebase_uid(firebase_uid)

        if not user:
            # 3. Si no existe, crearlo (Registro)
            logger.info(f"Creando nuevo usuario en Postgres para UID: {firebase_uid}")
            new_user = User(
                firebase_uid=firebase_uid,
                email=email,
                nombre=auth_data.nombre or nombre_firebase or "Usuario The Casa Chill & Coffe",
                telefono=auth_data.telefono,
                foto=foto_firebase
            )
            user = await self.repository.create(new_user)
        else:
            # Opcional: Actualizar datos si han cambiado en Firebase o en el request
            update_fields = {}
            if auth_data.nombre and auth_data.nombre != user.nombre:
                update_fields["nombre"] = auth_data.nombre
            if auth_data.telefono and auth_data.telefono != user.telefono:
                update_fields["telefono"] = auth_data.telefono
            
            if update_fields:
                user = await self.repository.update(user.id, update_fields)

        # 4. Retornar Perfil
        return AuthResponse(
            user=UserProfile(**user.model_dump())
        )

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_profile(self, user_id: str) -> UserProfile:
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UserProfile(**user.model_dump())

    async def update_profile(self, user_id: str, update_data: dict) -> UserProfile:
        user = await self.repository.update(user_id, update_data)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UserProfile(**user.model_dump())

    async def add_address(self, user_id: str, address_in: any) -> dict:
        return await self.repository.add_address(user_id, address_in.model_dump())

    async def remove_address(self, user_id: str, address_id: str):
        if not await self.repository.delete_address(user_id, address_id):
            raise HTTPException(status_code=404, detail="Dirección no encontrada")

    async def add_to_favorites(self, user_id: str, product_id: str):
        await self.repository.add_favorite(user_id, product_id)

    async def remove_from_favorites(self, user_id: str, product_id: str):
        await self.repository.remove_favorite(user_id, product_id)

    async def list_favorites(self, user_id: str) -> List[str]:
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user.favoritos

    async def change_password(self, user_id: str, old_pwd: str, new_pwd: str):
        raise HTTPException(status_code=400, detail="El cambio de contraseña debe gestionarse a través de Firebase")
