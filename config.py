from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Production-MCP-Server"
    
    # env="..." 대신 validation_alias="..." 사용
    CSV_FILE_PATH: str = Field(..., validation_alias="CSV_FILE_PATH")
    API_TOKEN: str = Field(..., validation_alias="MCP_API_TOKEN") 
    
    LOG_LEVEL: str = "INFO"
    PAGE_SIZE_DEFAULT: int = 10
    PAGE_SIZE_MAX: int = 100

    # Pydantic V2 설정 방식 (SettingsConfigDict 사용)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  # 대소문자 구분 (필수)
        extra="ignore"        # 정의되지 않은 환경변수는 무시 (에러 방지)
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()