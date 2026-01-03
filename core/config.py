import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    local_ai_url: str = os.getenv("LOCAL_AI_URL", "http://local-ai-router:8000")
    local_ai_api_key: str = os.getenv("LOCAL_AI_API_KEY", "")
    
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    sonarr_url: str = os.getenv("SONARR_URL", "http://sonarr:8989")
    sonarr_api_key: str = os.getenv("SONARR_API_KEY", "")
    
    radarr_url: str = os.getenv("RADARR_URL", "http://radarr:7878")
    radarr_api_key: str = os.getenv("RADARR_API_KEY", "")
    
    plex_url: str = os.getenv("PLEX_URL", "http://plex:32400")
    plex_token: str = os.getenv("PLEX_TOKEN", "")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
