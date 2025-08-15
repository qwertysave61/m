import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    POSTGRES_HOST: str = os.getenv("PGHOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("PGPORT", "5432"))
    POSTGRES_DB: str = os.getenv("PGDATABASE", "bot_factory")
    POSTGRES_USER: str = os.getenv("PGUSER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("PGPASSWORD", "")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Payment Configuration
    PAYMENT_PROVIDER_TOKEN: str = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    
    # File Storage
    BOT_STORAGE_PATH: str = os.getenv("BOT_STORAGE_PATH", "./running_bots")
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "./uploads")
    LOG_PATH: str = os.getenv("LOG_PATH", "./logs")
    
    # Bot Factory Configuration
    MAX_BOTS_PER_USER: int = int(os.getenv("MAX_BOTS_PER_USER", "10"))
    DEFAULT_BOT_CREATION_FEE: int = int(os.getenv("DEFAULT_BOT_CREATION_FEE", "50000"))
    DEFAULT_DAILY_FEE: int = int(os.getenv("DEFAULT_DAILY_FEE", "1000"))
    
    # Notification Configuration
    NOTIFICATION_DAYS_BEFORE: list[int] = [3, 1]
    CLEANUP_DAYS_AFTER: int = 15
    
    # External APIs
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    CURRENCY_API_KEY: str = os.getenv("CURRENCY_API_KEY", "")
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
