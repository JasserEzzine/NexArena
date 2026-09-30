from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    agent_enrollment_key: str
    demo_password: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    heartbeat_timeout: int = 30
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")


settings = Settings()
if len(settings.jwt_secret) < 32:
    raise RuntimeError("JWT_SECRET must contain at least 32 characters")
