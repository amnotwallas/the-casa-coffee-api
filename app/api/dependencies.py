from fastapi import Header, HTTPException, Depends
from typing import Optional
from sqlmodel import Session
from app.core.database import get_session
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.support_repo import SupportRepository
from app.services.product_service import ProductService
from app.services.user_service import AuthService, UserService
from app.services.order_service import CartService, OrderService
from app.services.support_service import SupportService, AdminService
from app.ai.providers.groq_provider import GroqProvider
from app.ai.services.agent_service import AgentService

# --- PROVIDERS ---
_ai_provider = GroqProvider()

# --- REPOSITORY FACTORIES ---

def get_user_repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)

def get_product_repo(session: Session = Depends(get_session)) -> ProductRepository:
    return ProductRepository(session)

def get_order_repo(session: Session = Depends(get_session)) -> OrderRepository:
    return OrderRepository(session)

def get_support_repo(session: Session = Depends(get_session)) -> SupportRepository:
    return SupportRepository(session)

# --- SERVICE FACTORIES ---

def get_product_service(repo: ProductRepository = Depends(get_product_repo)) -> ProductService:
    return ProductService(repository=repo)

def get_auth_service(repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(repository=repo)

def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(repository=repo)

def get_cart_service(
    order_repo: OrderRepository = Depends(get_order_repo), 
    product_repo: ProductRepository = Depends(get_product_repo)
) -> CartService:
    return CartService(order_repo=order_repo, product_repo=product_repo)

def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repo), 
    cart_service: CartService = Depends(get_cart_service)
) -> OrderService:
    return OrderService(order_repo=order_repo, cart_service=cart_service)

def get_support_service(repo: SupportRepository = Depends(get_support_repo)) -> SupportService:
    return SupportService(repository=repo)

def get_admin_service(
    support_repo: SupportRepository = Depends(get_support_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    order_repo: OrderRepository = Depends(get_order_repo)
) -> AdminService:
    return AdminService(
        support_repo=support_repo,
        product_repo=product_repo,
        order_repo=order_repo
    )

def get_agent_service(
    product_repo: ProductRepository = Depends(get_product_repo)
) -> AgentService:
    return AgentService(
        ai_provider=_ai_provider,
        product_repo=product_repo
    )

from app.core.firebase import verify_firebase_token

# --- SECURITY DEPENDENCIES ---

def get_current_user(
    authorization: str = Header(None), 
    required: bool = True,
    user_repo: UserRepository = Depends(get_user_repo)
) -> Optional[dict]:
    """Valida el token de Firebase y extrae el usuario de la DB local."""
    if not authorization or not authorization.startswith("Bearer "):
        if required:
            raise HTTPException(status_code=401, detail="Token faltante o inválido.")
        return None
    
    try:
        token = authorization.split(" ")[1]
        
        # 1. Verificar Token con Firebase Admin
        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            if required:
                raise HTTPException(status_code=401, detail="Token de Firebase inválido o expirado.")
            return None
        
        firebase_uid = decoded_token.get("uid")
        
        # 2. Buscar usuario en Postgres por firebase_uid
        user = user_repo.find_by_firebase_uid(firebase_uid)
        
        if user:
            return user.model_dump()
                
        if required:
            raise HTTPException(status_code=401, detail="Usuario no registrado en el sistema local.")
        return None
    except Exception:
        if required:
            raise HTTPException(status_code=401, detail="Error al validar identidad.")
        return None

def get_current_user_required(
    authorization: str = Header(None),
    user_repo: UserRepository = Depends(get_user_repo)
) -> dict:
    return get_current_user(authorization, required=True, user_repo=user_repo)

def get_current_user_optional(
    authorization: str = Header(None),
    user_repo: UserRepository = Depends(get_user_repo)
) -> Optional[dict]:
    return get_current_user(authorization, required=False, user_repo=user_repo)
