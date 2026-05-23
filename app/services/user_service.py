from typing import Optional, List
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.schemas.user_schema import FirebaseAuthRequest, AuthResponse, UserProfile
from app.core.logger import get_logger
from app.core.firebase import verify_firebase_token
from app.core.security import create_access_token
from app.core.exceptions import EntityNotFoundException, UnauthorizedException, BusinessLogicException

logger = get_logger(__name__)

class AuthService:
    """
    Service layer for authentication and user synchronization.
    """
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def verify_and_sync_user(self, auth_data: FirebaseAuthRequest) -> AuthResponse:
        """
        Verify Firebase token and synchronize local user profile.
        """
        logger.info("Starting Firebase token verification")
        
        decoded_token = verify_firebase_token(auth_data.firebase_token)
        if not decoded_token:
            logger.warning("Invalid or expired Firebase token")
            raise UnauthorizedException(message="Invalid Firebase token")
        
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        firebase_name = decoded_token.get("name")
        firebase_picture = decoded_token.get("picture")

        # 1. Intentar encontrar por Firebase UID (lo más rápido)
        user = await self.repository.find_by_firebase_uid(firebase_uid)

        # 2. Si no hay UID, intentar encontrar por Email (para evitar duplicados)
        if not user and email:
            user = await self.repository.find_by_email(email)
            if user:
                logger.info(f"Linking existing email {email} to new Firebase UID: {firebase_uid}")
                user = await self.repository.update(user.id, {"firebase_uid": firebase_uid})

        # 3. Si sigue sin existir, crearlo (Registro Automático)
        if not user:
            logger.info(f"Creating new user for UID: {firebase_uid}")
            
            # Lógica de nombre por defecto: Request -> Token Firebase -> Email -> Genérico
            fallback_name = email.split("@")[0].capitalize() if email else "Café Lover"
            display_name = auth_data.nombre or firebase_name or fallback_name

            new_user = User(
                firebase_uid=firebase_uid,
                email=email,
                nombre=display_name,
                telefono=auth_data.telefono,
                foto=firebase_picture
            )
            user = await self.repository.create(new_user)
            # Recargar para inicializar relaciones
            user = await self.repository.find_by_id(user.id)
        else:
            # 4. Si ya existe, actualizar campos básicos si cambiaron
            update_fields = {}
            if auth_data.nombre and auth_data.nombre != user.nombre:
                update_fields["nombre"] = auth_data.nombre
            if auth_data.telefono and auth_data.telefono != user.telefono:
                update_fields["telefono"] = auth_data.telefono
            
            if update_fields:
                user = await self.repository.update(user.id, update_fields)

        # 5. Generar Token de Acceso local (Intercambio)
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        return AuthResponse(
            user=UserProfile.model_validate(user),
            access_token=access_token
        )

class UserService:
    """
    Service layer for user profile and preferences management.
    """
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_profile(self, user_id: str) -> UserProfile:
        """
        Get user profile by internal ID.
        """
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException(message="User not found")
        return UserProfile.model_validate(user)

    async def update_profile(self, user_id: str, update_data: dict) -> UserProfile:
        """
        Update user profile details.
        """
        user = await self.repository.update(user_id, update_data)
        if not user:
            raise EntityNotFoundException(message="User not found")
        return UserProfile.model_validate(user)

    async def add_address(self, user_id: str, address_in: any) -> dict:
        """
        Add a shipping address to user profile.
        """
        return await self.repository.add_address(user_id, address_in.model_dump())

    async def remove_address(self, user_id: str, address_id: str):
        """
        Remove a shipping address from user profile.
        """
        if not await self.repository.delete_address(user_id, address_id):
            raise EntityNotFoundException(message="Address not found")

    async def add_to_favorites(self, user_id: str, product_id: str):
        """
        Add product to user favorites.
        """
        await self.repository.add_favorite(user_id, product_id)

    async def remove_from_favorites(self, user_id: str, product_id: str):
        """
        Remove product from user favorites.
        """
        await self.repository.remove_favorite(user_id, product_id)

    async def list_favorites(self, user_id: str) -> List[str]:
        """
        Get the list of product IDs in user favorites.
        Optimized to fetch only IDs.
        """
        return await self.repository.get_favorite_ids(user_id)

    async def change_password(self, user_id: str, old_pwd: str, new_pwd: str):
        """
        Password management is delegated to Firebase.
        """
        raise BusinessLogicException(message="Password changes must be managed through Firebase")
