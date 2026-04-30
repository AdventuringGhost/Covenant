# Configuration: load all env vars (DB, OPA, Claude API, JWT, Azure) via pydantic-settings

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str
    opa_url: str = "http://localhost:8181"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    claude_model: str = "claude-sonnet-4-6"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
