import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import engine, init_db
from app.models.user import User, Address, Preference
from app.models.product import Product, Category, Nutrition, Customization, CustomizationOption
from app.models.support import Review, StoreInfo, StoreSchedule

def load_json_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def migrate_categories(session: AsyncSession, categories: List[Dict[str, Any]]):
    print("-> Migrando categorías...")
    for cat_data in categories:
        existing = await session.get(Category, cat_data["id"])
        if not existing:
            new_cat = Category(id=cat_data["id"], nombre=cat_data["nombre"])
            session.add(new_cat)
    await session.commit()

async def migrate_users(session: AsyncSession, users: List[Dict[str, Any]]):
    print("-> Migrando usuarios...")
    for u in users:
        # Check by ID or Email
        stmt = select(User).where((User.id == u["id"]) | (User.email == u["email"]))
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if not existing:
            # Determine if admin based on email or flag
            is_admin = u.get("is_admin", False) or u["email"].endswith("@thecasa.com")
            
            user = User(
                id=u["id"],
                firebase_uid=f"seed_uid_{u['id'][:8]}",
                nombre=u["nombre"],
                email=u["email"],
                is_admin=is_admin,
                telefono=u.get("telefono"),
                foto=u.get("foto")
            )
            session.add(user)
            
            # Migrar Preferencias
            pref_data = u.get("preferencias", {})
            session.add(Preference(
                user_id=user.id,
                notificacionesPush=pref_data.get("notificacionesPush", True),
                tipoLecheFavorita=pref_data.get("tipoLecheFavorita", "Almendra"),
                idioma=pref_data.get("idioma", "es")
            ))
            
            # Migrar Direcciones
            for addr in u.get("direcciones", []):
                session.add(Address(
                    user_id=user.id,
                    calle=addr["calle"],
                    ciudad=addr["ciudad"],
                    codigoPostal=addr["codigoPostal"],
                    referencia=addr.get("referencia"),
                    esDefault=addr.get("esDefault", False)
                ))
    await session.commit()

async def migrate_products(session: AsyncSession, products: List[Dict[str, Any]]):
    print("-> Migrando productos y detalles...")
    for p in products:
        existing = await session.get(Product, p["id"])
        if not existing:
            product = Product(
                id=p["id"],
                nombre=p["nombre"],
                descripcion=p["descripcion"],
                precio=p["precio"],
                intensidad=p["intensidad"],
                imagenes=p.get("imagenes", []),
                category_id=p.get("category_id"),
                ingredientes=p.get("ingredientes", []),
                rating_avg=p.get("rating_avg", 0.0),
                reviews_count=p.get("reviews_count", 0),
                disponible=p.get("disponible", True)
            )
            session.add(product)
            
            # 1. Migrar Nutrición
            nutri = p.get("valores_nutricionales", {})
            if nutri:
                session.add(Nutrition(
                    product_id=product.id,
                    calorias=int(nutri.get("calorias", 0)),
                    proteinas=float(nutri.get("proteinas", 0.0)),
                    grasas=float(nutri.get("grasas", 0.0)),
                    carbohidratos=float(nutri.get("carbohidratos", 0.0) or 0.0)
                ))
            
            # 2. Migrar Personalizaciones
            for cust_data in p.get("personalizaciones", []):
                cust = Customization(
                    product_id=product.id,
                    tipo=cust_data["tipo"]
                )
                session.add(cust)
                await session.flush()
                
                for opt_data in cust_data.get("opciones", []):
                    session.add(CustomizationOption(
                        customization_id=cust.id,
                        nombre=opt_data["nombre"],
                        extra_precio=float(opt_data.get("extra_precio", 0.0)),
                        valor=str(opt_data.get("valor", "")) if opt_data.get("valor") else None
                    ))
    await session.commit()

async def migrate_reviews(session: AsyncSession, reviews_map: Dict[str, List[Dict[str, Any]]]):
    print("-> Migrando reseñas...")
    for product_id, reviews in reviews_map.items():
        for r in reviews:
            existing = await session.get(Review, r["id"])
            if not existing:
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
        store = StoreInfo(
            id=1,
            nombre=info["nombre"],
            direccion=info["direccion"],
            telefono=info["telefono"],
            email=info["email"],
            estaAbierto=info.get("estaAbierto", True),
            tiempo_espera_actual=info.get("tiempo_espera_actual", 15),
            volumen_pedidos=info.get("volumen_pedidos", "medio")
        )
        session.add(store)
        
        for h in info.get("horarios", []):
            session.add(StoreSchedule(
                store_id=1,
                dia=h["dia"],
                apertura=h["apertura"],
                cierre=h["cierre"],
                abierto=h.get("abierto", True)
            ))
    await session.commit()

async def seed_database():
    print("🚀 Iniciando siembra de base de datos (100% Relacional)")
    
    await init_db()
    data = load_json_data("app/data/coffee-data.json")
    
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            await migrate_categories(session, data.get("categories", []))
            await migrate_users(session, data.get("users", []))
            await migrate_products(session, data.get("products", []))
            await migrate_reviews(session, data.get("reviews", {}))
            await migrate_store_info(session, data.get("store_info", {}))
            
            await session.commit()
            print("✅ ¡Siembra completada con éxito!")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error durante la siembra: {e}")

if __name__ == "__main__":
    asyncio.run(seed_database())
