"""
config.py
Central settings object. Everything else imports from here instead of
reading env vars directly, so there's one place to change when you
move from local Docker -> staging -> wherever.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    postgres_user: str = "ocular"
    postgres_password: str = "ocular"
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
