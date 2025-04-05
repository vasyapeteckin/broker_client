from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseBrokerSettings(BaseSettings):
    URL: SecretStr = Field(alias="BROKER_URL", default="amqp://guest:guest@localhost/")

    model_config = SettingsConfigDict(extra='allow', env_file=('.env.dev', '.env'))

    @property
    def url_str(self) -> str:
        return self.URL.get_secret_value()