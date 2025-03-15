from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    NBA_API_KEY: str
    ELEVEN_LABS_API_KEY: str
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 