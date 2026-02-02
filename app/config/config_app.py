from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    # DB parts (used if full URLs are not provided)
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str


    # Security / JWT
    SECRET: str
    SECRET_CONFIRM_KEY: str
    SECRET_RESET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    FRONT_URL: str
    
    
    # MinIO
    BUCKET: str = "permanent"

    # pika
    PIKA_HOST: str
    PIKA_PORT: int
    PIKA_USER: str
    PIKA_PASSWORD: str
    PIKA_INCOMING_QUEUE: str
    PIKA_OUTGOING_QUEUE: str


    UKASSA_URL: str
    UKASSA_SHOP_ID: str
    UKASSA_SECRET_KEY: str

    @computed_field
    @property
    def pika_url(self) -> str:
      return f"amqp://{self.PIKA_USER}:{self.PIKA_PASSWORD}@{self.PIKA_HOST}:{self.PIKA_PORT}/"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def sync_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @computed_field
    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @computed_field
    @property
    def test_sync_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.TEST_DATABASE_NAME}"
        )

    @computed_field
    @property
    def test_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.TEST_DATABASE_NAME}"
        )

settings = Settings()

