import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
from app.core.logger import get_logger
import os

logger = get_logger(__name__)

def init_firebase():
    """Inicializa Firebase Admin SDK."""
    try:
        if not firebase_admin._apps:
            if settings.FIREBASE_CREDENTIALS and os.path.exists(settings.FIREBASE_CREDENTIALS):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin inicializado con service account.")
            else:
                # Intenta inicializar con credenciales por defecto (útil en entornos como GCP)
                # o simplemente falla si no hay configuración
                try:
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin inicializado con credenciales por defecto.")
                except Exception:
                    logger.warning("No se detectó FIREBASE_CREDENTIALS. La validación de tokens fallará.")
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {e}")

def verify_firebase_token(token: str) -> dict:
    """Verifica un token de Firebase y retorna el payload decodificado."""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Error al verificar token de Firebase: {e}")
        return None
