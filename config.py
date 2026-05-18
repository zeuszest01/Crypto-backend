from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/zzlwr_trading"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-here-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Groq AI
    GROQ_API_KEY: str = ""
    
    # Broker
    BROKER_EA_HOST: str = "localhost"
    BROKER_EA_PORT: int = 8888
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Encryption
    ENCRYPTION_KEY: str = ""
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
