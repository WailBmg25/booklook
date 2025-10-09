from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
     # Defining settings with Pydantic
     APP_NAME: str
     APP_VERSION: str
     POSTGRES_URI: str
     POSTGRES_DB_NAME: str

     class Config:  # Configuration for Pydantic settings
        env_file = ".env"

def get_settings() -> Settings:
    # Function to get settings instance
    return Settings()
