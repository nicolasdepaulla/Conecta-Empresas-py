from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str
    mongo_db_name: str = "conecta_empresas"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    payment_provider_api_key: str = ""
    payment_provider_webhook_secret: str = ""

    # URL pública do backend (ex.: a gerada pelo ngrok) usada como notification_url
    # nas preferências do Mercado Pago. Deixe vazio para não enviar notification_url
    # (o Mercado Pago então usa a configurada no painel de Webhooks, se houver).
    public_base_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
