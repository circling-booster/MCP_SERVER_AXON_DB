from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Production-MCP-Server"
    CSV_FILE_PATH: str = Field(..., env="CSV_FILE_PATH")
    API_TOKEN: str = Field(..., env="MCP_API_TOKEN") # 필수값 강제
    LOG_LEVEL: str = "INFO"
    PAGE_SIZE_DEFAULT: int = 10
    PAGE_SIZE_MAX: int = 100

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()