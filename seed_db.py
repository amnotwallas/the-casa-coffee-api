import json
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.user import User
from app.models.product import Product
from app.models.support import Review, StoreInfo

def load_json_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def migrate_users(session: Session, users: List[Dict[str, Any]]):
    print("-> Migrando usuarios...")
    for u in users:
        if not session.get(User, u["id"]):
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

def migrate_products(session: Session, products: List[Dict[str, Any]]):
    print("-> Migrando productos...")
    for p in products:
        if not session.get(Product, p["id"]):
            # Filtramos campos que coincidan exactamente con el modelo
            valid_data = {k: v for k, v in p.items() if k in Product.__fields__}
            session.add(Product(**valid_data))

def migrate_reviews(session: Session, reviews_map: Dict[str, List[Dict[str, Any]]]):
    print("-> Migrando reseñas...")
    for product_id, reviews in reviews_map.items():
        for r in reviews:
            if not session.get(Review, r["id"]):
                fecha_dt = datetime.fromisoformat(r["fecha"].replace("Z", "+00:00"))
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

def migrate_store_info(session: Session, info: Dict[str, Any]):
    print("-> Migrando info de la tienda...")
    if info and not session.get(StoreInfo, 1):
        session.add(StoreInfo(id=1, **info))

def seed_database():
    print("🚀 Iniciando siembra de base de datos (JSON -> Postgres)")
    
    # Asegurar que las tablas existan
    init_db()
    
    # Cargar datos
    data = load_json_data("app/data/coffee-data.json")
    
    with Session(engine) as session:
        try:
            migrate_users(session, data.get("users", []))
            migrate_products(session, data.get("products", []))
            migrate_reviews(session, data.get("reviews", {}))
            migrate_store_info(session, data.get("store_info", {}))
            
            session.commit()
            print("✅ ¡Migración completada con éxito!")
        except Exception as e:
            session.rollback()
            print(f"❌ Error durante la migración: {e}")

if __name__ == "__main__":
    seed_database()
