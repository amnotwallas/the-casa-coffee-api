from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

class Settings(BaseSettings):
    # --- Project Metadata ---
    APP_NAME: str = "The Casa Chill & Coffe API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # --- Firebase Configuration ---
    FIREBASE_CREDENTIALS: Optional[str] = None # Path to service account JSON
    SECRET_KEY: str = "dev_secret_key_64_chars_long_placeholder"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    ADMIN_SECRET_TOKEN: str = "dev_admin_token_placeholder"
    DATABASE_URL: str = "" # Injected from environment (Supabase)
    
    # --- AI Configuration (Groq) ---
    GROQ_API_KEY: str = "" 
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # --- Server & Logging ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    LOG_LEVEL: int = logging.INFO
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
