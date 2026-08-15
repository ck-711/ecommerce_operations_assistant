from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'Ecommerce Operations Assistant'
    environment: str = 'development'
    jwt_secret: str = 'change-me-in-production'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 60
    database_url: str = 'sqlite:///./ecommerce.db'
    redis_url: str = 'redis://localhost:6379/0'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
