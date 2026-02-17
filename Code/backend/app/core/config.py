from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    ENV: str

    MONGO_URI: str
    MONGO_DB_NAME: str
    ADMIN_SECRET_KEY: str
    class Config:
        env_file = ".env"

settings = Settings()