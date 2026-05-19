from fastapi import Header, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.support_repo import SupportRepository
from app.services.product_service import ProductService
from app.services.user_service import AuthService, UserService
from app.services.order_service import CartService, OrderService
from app.services.support_service import SupportService
from app.services.admin_service import AdminService
from app.ai.providers.groq_provider import GroqProvider
from app.ai.services.agent_service import AgentService
from app.core.firebase import verify_firebase_token

# --- PROVIDERS ---
_ai_provider = GroqProvider()

# --- REPOSITORY FACTORIES ---

def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """
    Factory for UserRepository injected with a database session.
    """
    return UserRepository(session)

def get_product_repo(session: AsyncSession = Depends(get_session)) -> ProductRepository:
    """
    Factory for ProductRepository injected with a database session.
    """
    return ProductRepository(session)

def get_order_repo(session: AsyncSession = Depends(get_session)) -> OrderRepository:
    """
    Factory for OrderRepository injected with a database session.
    """
    return OrderRepository(session)

def get_support_repo(session: AsyncSession = Depends(get_session)) -> SupportRepository:
    """
    Factory for SupportRepository injected with a database session.
    """
    return SupportRepository(session)

# --- SERVICE FACTORIES ---

def get_product_service(repo: ProductRepository = Depends(get_product_repo)) -> ProductService:
    """
    Factory for ProductService.
    """
    return ProductService(repository=repo)

def get_auth_service(repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    """
    Factory for AuthService.
    """
    return AuthService(repository=repo)

def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    """
    Factory for UserService.
    """
    return UserService(repository=repo)

def get_cart_service(
    order_repo: OrderRepository = Depends(get_order_repo), 
    product_repo: ProductRepository = Depends(get_product_repo)
) -> CartService:
    """
    Factory for CartService.
    """
    return CartService(order_repo=order_repo, product_repo=product_repo)

def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repo), 
    cart_service: CartService = Depends(get_cart_service),
    user_repo: UserRepository = Depends(get_user_repo),
    product_repo: ProductRepository = Depends(get_product_repo)
) -> OrderService:
    """
    Factory for OrderService with required dependencies.
    """
    return OrderService(
        order_repo=order_repo, 
        cart_service=cart_service, 
        user_repo=user_repo,
        product_repo=product_repo
    )

def get_support_service(repo: SupportRepository = Depends(get_support_repo)) -> SupportService:
    """
    Factory for SupportService.
    """
    return SupportService(repository=repo)

def get_admin_service(
    support_repo: SupportRepository = Depends(get_support_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    order_repo: OrderRepository = Depends(get_order_repo)
) -> AdminService:
    """
    Factory for AdminService.
    """
    return AdminService(
        support_repo=support_repo,
        product_repo=product_repo,
        order_repo=order_repo
    )

def get_agent_service(
    product_repo: ProductRepository = Depends(get_product_repo)
) -> AgentService:
    """
    Factory for AgentService.
    """
    return AgentService(
        ai_provider=_ai_provider,
        product_repo=product_repo
    )

# --- SECURITY DEPENDENCIES ---

async def get_current_user(
    authorization: str = Header(None), 
    required: bool = True,
    user_repo: UserRepository = Depends(get_user_repo)
) -> Optional[dict]:
    """
    Validate Firebase ID token and retrieve the user from the local database.
    """
    if not authorization or not authorization.startswith("Bearer "):
        if required:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication token.")
        return None
    
    try:
        token = authorization.split(" ")[1]
        
        # 1. Verify token with Firebase Admin
        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            if required:
                raise HTTPException(status_code=401, detail="Firebase token expired or invalid.")
            return None
        
        firebase_uid = decoded_token.get("uid")
        
        # 2. Sync with local database
        user = await user_repo.find_by_firebase_uid(firebase_uid)
        
        if user:
            return user.model_dump()
                
        if required:
            raise HTTPException(status_code=401, detail="User not registered in the local system.")
        return None
    except Exception:
        if required:
            raise HTTPException(status_code=401, detail="Identity validation failed.")
        return None

async def get_current_user_required(
    authorization: str = Header(None),
    user_repo: UserRepository = Depends(get_user_repo)
) -> dict:
    """
    Strict dependency for routes requiring an authenticated user.
    """
    return await get_current_user(authorization, required=True, user_repo=user_repo)

async def get_current_user_optional(
    authorization: str = Header(None),
    user_repo: UserRepository = Depends(get_user_repo)
) -> Optional[dict]:
    """
    Optional dependency for routes that change behavior based on authentication status.
    """
    return await get_current_user(authorization, required=False, user_repo=user_repo)
