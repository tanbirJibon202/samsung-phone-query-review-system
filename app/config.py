from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/samsung_phones"
    groq_api_key: str = ""
    # llama-3.3-70b-versatile is Enterprise-tier only as of mid-2026; this
    # default is Groq's recommended free/developer-tier model.
    groq_model: str = "openai/gpt-oss-120b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
