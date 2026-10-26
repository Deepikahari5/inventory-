from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Inventory Management API"
    database_url: str = "mysql+pymysql://root:password@localhost:3306/inventory_db"
    secret_key: str = "change-this-secret-key-use-at-least-32-characters"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    default_page_size: int = 10
    max_page_size: int = 100
    max_page_number: int = 1_000_000
    max_search_length: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
