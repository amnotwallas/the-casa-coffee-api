import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, init_db
from app.models.user import User
from app.models.product import Product
from app.models.support import Review, StoreInfo

def load_json_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def migrate_users(session: AsyncSession, users: List[Dict[str, Any]]):
    print("-> Migrando usuarios...")
    for u in users:
        existing = await session.get(User, u["id"])
        if not existing:
            session.add(User(
                id=u["id"],
                firebase_uid=f"seed_uid_{u['id'][:8]}",
                nombre=u["nombre"],
                email=u["email"],
                telefono=u.get("telefono"),
                foto=u.get("foto"),
                direcciones=u.get("direcciones", []),
                favoritos=u.get("favoritos", [])
            ))

async def migrate_products(session: AsyncSession, products: List[Dict[str, Any]]):
    print("-> Migrando productos...")
    for p in products:
        existing = await session.get(Product, p["id"])
        if not existing:
            # Filtramos campos que coincidan exactamente con el modelo
            valid_data = {k: v for k, v in p.items() if k in Product.__fields__ or k in Product.model_fields}
            session.add(Product(**valid_data))

async def migrate_reviews(session: AsyncSession, reviews_map: Dict[str, List[Dict[str, Any]]]):
    print("-> Migrando reseñas...")
    for product_id, reviews in reviews_map.items():
        for r in reviews:
            existing = await session.get(Review, r["id"])
            if not existing:
                # Hacer la fecha "naive" (sin zona horaria) para evitar errores con asyncpg
                # ya que el modelo usa TIMESTAMP WITHOUT TIME ZONE
                fecha_dt = datetime.fromisoformat(r["fecha"].replace("Z", "+00:00")).replace(tzinfo=None)
                session.add(Review(
                    id=r["id"],
                    product_id=product_id,
                    user_id=r["userId"],
                    user_name=r["userName"],
                    rating=r["rating"],
                    comentario=r["comentario"],
                    fotos=r.get("fotos", []),
                    fecha=fecha_dt,
                    helpful_count=r.get("helpful_count", 0)
                ))

async def migrate_store_info(session: AsyncSession, info: Dict[str, Any]):
    print("-> Migrando info de la tienda...")
    existing = await session.get(StoreInfo, 1)
    if info and not existing:
        session.add(StoreInfo(id=1, **info))

async def seed_database():
    print("🚀 Iniciando siembra de base de datos (JSON -> Postgres)")
    
    # Asegurar que las tablas existan (init_db ahora es async)
    await init_db()
    
    # Cargar datos
    data = load_json_data("app/data/coffee-data.json")
    
    # Crear sesión asíncrona manualmente para el script
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            await migrate_users(session, data.get("users", []))
            await migrate_products(session, data.get("products", []))
            await migrate_reviews(session, data.get("reviews", {}))
            await migrate_store_info(session, data.get("store_info", {}))
            
            await session.commit()
            print("✅ ¡Migración completada con éxito!")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error durante la migración: {e}")

if __name__ == "__main__":
    asyncio.run(seed_database())
