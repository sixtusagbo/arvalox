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

    # Paystack
    paystack_secret_key: str = ""
    paystack_public_key: str = ""
    paystack_webhook_secret: str = ""

    # Environment
    environment: str = "development"
    debug: bool = True

    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated origins string into list"""
        if self.debug:
            # In development, be more permissive
            return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_parse_none_str": "None",
    }


settings = Settings()
