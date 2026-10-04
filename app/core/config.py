from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # "development" ou "production" -- controla comportamentos sensíveis ao
    # ambiente, como o atributo `secure` do cookie de autenticação.
    ambiente: str = "development"

    # Postgres -- banco único da aplicação (migração de MongoDB concluída:
    # os 4 repositories, usuario/sessao/pacote/pedido, já usam este banco).
    database_url: str = "postgresql+asyncpg://conecta:conecta@localhost:5433/conecta_empresas"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    payment_provider_api_key: str = ""
    payment_provider_webhook_secret: str = ""

    # URL pública onde a aplicação está acessível (ex.: link do ngrok em
    # desenvolvimento). Usada para montar links absolutos, como o de
    # redefinição de senha enviado por e-mail.
    public_base_url: str = "http://localhost:8000"

    # E-mail (SMTP do Gmail) -- usado para o "esqueci minha senha"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    class Config:
        env_file = ".env"

    @property
    def is_production(self) -> bool:
        return self.ambiente.lower() == "production"


settings = Settings()
