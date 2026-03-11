from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5"

    # Database
    db_connection_string: str = ""
    sqlite_database_path: str = "./your_database.db"

    # App
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
