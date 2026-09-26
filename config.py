"""
config.py
Central settings object. Everything else imports from here instead of
reading env vars directly, so there's one place to change when you
move from local Docker -> staging -> wherever.
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")
SMTP_PORT = os.getenv("SMTP_PORT")



class Settings(BaseSettings):
    # Postgres
    postgres_user: str = "postgres"
    postgres_password: str = "postgresdara"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ocular"

    # Redis (Celery broker + result backend)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # FAISS
    faiss_index_path: str = "./data/faiss_index.bin"
    faiss_dim: int = 512  # ArcFace embedding size

    # Recognition threshold (cosine similarity, since vectors are L2-normalized)
    recognition_threshold: float = 0.45



    #secret key for JWT token generation
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

    # SMTP settings for email sending
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = int(SMTP_PORT) if SMTP_PORT else 587
    smtp_user: str | None = SMTP_USER
    smtp_password: str | None = SMTP_PASSWORD
    smtp_from: str | None = SMTP_FROM


    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"


settings = Settings()
