from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "aller_scan"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
