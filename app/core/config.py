from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VAM Capital Core API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Resend Email Settings
    RESEND_API_KEY: str = "re_DMXyvxKR_NxgZLujmr9FN6bpegYpfhSR5"
    EMAILS_FROM_EMAIL: str = "no-reply@vamcapital.in"
    EMAILS_FROM_NAME: str = "VAM Capital Support"

    # JWT Authentication
    SECRET_KEY: str = "6ac436e6ffaf42151316292df18d67a4d3f1a075343f97e862de834ec6ca21cf"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # PostgreSQL (Using explicit psycopg2 driver)
    DATABASE_URL: str = (
        "postgresql://neondb_owner:npg_naLfCcX4s9Ek@ep-bitter-mountain-b5wqzrv8-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require   "
    )

    # Expose SQLALCHEMY_DATABASE_URI for direct ORM access
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://vamcapital.in",
        "https://www.vamcapital.in",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()