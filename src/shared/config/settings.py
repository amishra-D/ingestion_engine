from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URI: str
    ALGORITHM: str
    SECRET_KEY: str
    AUTO_INGESTION: bool = True
    INGESTION_INTERVAL: float = 2.0
    MIN_POOL_SIZE: int = 5
    MAX_POOL_SIZE:int = 20
    class Config:
        env_file = ".env"


settings = Settings()