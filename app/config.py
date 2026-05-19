from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_token: str

    llm_base_url: str
    llm_api_key: str
    llm_model: str = "gpt-4o-mini"

    todoist_api_token: str
    todoist_project_id: str | None = None

    aggregation_window_seconds: float = 30.0

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
