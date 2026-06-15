from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# Resolve .env relative to this file, not the CWD
ENV_FILE = Path(__file__).resolve().parents[4] / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI News-to-Carousel Automation Platform"
    
    # Database
    DATABASE_URL: str           # postgresql://... (used by Alembic/sync)
    SYNC_DATABASE_URL: str
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Derive async URL from DATABASE_URL by injecting the asyncpg driver."""
        async_url = self.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        ).replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        )
        # asyncpg doesn't understand sslmode or channel_binding
        return async_url.replace("sslmode=require", "ssl=require").replace("&channel_binding=require", "")
    
    # Redis
    REDIS_URL: str
    
    # APIs
    OPENAI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    
    # Meta
    META_GRAPH_API_URL: str = "https://graph.facebook.com/v19.0"
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    
    # Gemini / Gemma
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    COHERE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemma-4-31b-it"
    
    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3-70b-instruct"
    
    # Qdrant Cloud
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    
    # Cloudflare R2
    CLOUDFLARE_R2_ACCESS_KEY_ID: str = ""
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_ENDPOINT_URL: str = ""
    CLOUDFLARE_R2_BUCKET_NAME: str = ""
    CLOUDFLARE_R2_PUBLIC_URL: str = ""
    
    # Security
    ENCRYPTION_KEY: str = "BIn4i0m5A7Y4xWJzD3z9r0KzL1e3N9v4M3b2A1V8c2Q=" # Fallback key for dev, should be 32 url-safe base64
    FRONTEND_URL: str = "http://localhost:3000"
    FIREBASE_CREDENTIALS_PATH: str = "socialpx-admin.json"
    
    # Upload Settings
    MAX_BACKGROUND_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
