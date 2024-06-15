from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URI: str = ''

    class Config:
        env_file: str = ".env"


settings = Settings()
