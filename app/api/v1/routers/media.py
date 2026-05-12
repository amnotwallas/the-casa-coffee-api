import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/media", tags=["Media"])

# Directorio base para archivos estáticos
STATIC_DIR = os.path.join(os.getcwd(), "app/data/static")

def serve_file(folder: str, file_name: str):
    """Función genérica para servir archivos estáticos con validación de seguridad."""
    folder_path = os.path.join(STATIC_DIR, folder)
    file_path = os.path.join(folder_path, file_name)
    
    # --- SEGURIDAD: Evitar Directory Traversal ---
    abs_base = os.path.abspath(folder_path)
    abs_target = os.path.abspath(file_path)
    
    if not abs_target.startswith(abs_base):
        logger.warning(f"Intento de acceso no autorizado a ruta: {file_path}")
        raise HTTPException(status_code=400, detail="INVALID_PATH")

    if not os.path.exists(file_path):
        logger.info(f"Archivo no encontrado: {folder}/{file_name}")
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    return FileResponse(file_path)

@router.get("/products/{image_name}")
async def get_product_image(image_name: str):
    """Sirve imágenes de productos."""
    return serve_file("products", image_name)

@router.get("/promotions/{image_name}")
async def get_promotion_image(image_name: str):
    """Sirve imágenes de promociones."""
    return serve_file("promotions", image_name)

@router.get("/assets/{file_name}")
async def get_asset(file_name: str):
    """Sirve assets generales (iconos, logos, etc)."""
    return serve_file("assets", file_name)
