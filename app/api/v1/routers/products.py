from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.services.product_service import ProductService
from app.services.support_service import SupportService
from app.schemas.product_schema import Product, ProductListResponse
from app.schemas.support_schema import Review, ReviewCreate, ProductReviewsResponse
from app.api.dependencies import get_product_service, get_support_service, get_current_user_required

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service)
):
    products = await product_service.get_all_products(
        category=category, 
        search=search, 
        page=page, 
        limit=limit
    )
    total = await product_service.get_total_count(category=category, search=search)
    return {"data": products, "total": total, "page": page}

@router.get("/categories")
async def get_categories(product_service: ProductService = Depends(get_product_service)):
    return await product_service.get_categories()

@router.get("/featured", response_model=List[Product])
async def get_featured(product_service: ProductService = Depends(get_product_service)):
    return await product_service.get_featured_products()

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service)
):
    results = await product_service.get_all_products(search=q, page=page, limit=limit)
    total = await product_service.get_total_count(search=q)
    return {"results": results, "count": total}

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
):
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.get("/{product_id}/reviews", response_model=ProductReviewsResponse)
async def list_reviews(
    product_id: str,
    support_service: SupportService = Depends(get_support_service)
):
    return await support_service.get_product_reviews(product_id)

@router.post("/{product_id}/reviews", response_model=Review, status_code=201)
async def add_review(
    product_id: str,
    review_in: ReviewCreate,
    support_service: SupportService = Depends(get_support_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Añade una reseña usando la identidad real del usuario logueado."""
    return await support_service.add_product_review(
        product_id=product_id,
        user_id=current_user["id"],
        user_name=current_user["nombre"],
        review_in=review_in
    )
