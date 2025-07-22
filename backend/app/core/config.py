from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str
    test_database_url: str = ""

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Environment
    environment: str = "development"
    debug: bool = True

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_parse_none_str": "None",
    }


settings = Settings()
