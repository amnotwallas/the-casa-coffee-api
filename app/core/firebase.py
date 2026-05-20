import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
from app.core.logger import get_logger
import os
import json

logger = get_logger(__name__)

def init_firebase():
    """
    Initialize the Firebase Admin SDK.
    Supports local file path or JSON string in FIREBASE_CREDENTIALS.
    """
    try:
        if not firebase_admin._apps:
            if not settings.FIREBASE_CREDENTIALS:
                try:
                    # Attempt to initialize with default credentials (useful for GCP/Firebase environments)
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin initialized with default credentials.")
                except Exception:
                    logger.warning("FIREBASE_CREDENTIALS not found. Token validation will fail.")
                return

            # Check if it's a file path
            if os.path.exists(settings.FIREBASE_CREDENTIALS):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized from service account file.")
            else:
                # Try to parse as JSON string
                try:
                    cred_dict = json.loads(settings.FIREBASE_CREDENTIALS)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin initialized from environment JSON string.")
                except json.JSONDecodeError:
                    logger.error("FIREBASE_CREDENTIALS is neither a file path nor valid JSON.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")

def verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded payload.
    """
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Failed to verify Firebase token: {e}")
        return None
