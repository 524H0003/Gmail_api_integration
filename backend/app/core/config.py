import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./absent_requests.db"

    # Cookie configuration
    access_token_expire_minutes: int = 60
    access_token_cookie_key: str = "access_token"

    # Auth configuration
    jwt_secret_key: str = secrets.token_hex(16)

    # Google configuration
    google_credentials_path: str = "credentials.json"

    pubsub_oidc_topic: str = ""

    # App configuration
    manager_email: str = ""
    sender_email: str = ""
    email_template_file: str = "templates/absent_request.html"


settings = Settings()
