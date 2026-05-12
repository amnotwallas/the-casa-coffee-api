from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

class Settings(BaseSettings):
    # --- METADATA (Fijos en código) ---
    APP_NAME: str = "The Casa Chill & Coffe API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # --- FIREBASE ---
    FIREBASE_CREDENTIALS: Optional[str] = None # Path al archivo .json de Firebase
    SECRET_KEY: str = "dev_secret_key_64_chars_long_placeholder"
    ADMIN_SECRET_TOKEN: str = "dev_admin_token_placeholder"
    DATABASE_URL: str = "" # Inyectada desde Supabase
    
    # --- INTELIGENCIA ARTIFICIAL ---
    GROQ_API_KEY: str = "" # Opcional en dev, obligatoria en prod
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # --- SERVIDOR Y LOGS ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000" # Cambiar en producción
    LOG_LEVEL: int = logging.INFO
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
