from pydantic import Field
from pydantic_settings import BaseSettings


class TwilioSettings(BaseSettings):
    model_config = dict(env_prefix="TWILIO_", env_file=".env", extra="ignore")

    account_sid: str
    auth_token: str
    phone_number: str


class Settings(BaseSettings):
    model_config = dict(extra="ignore")

    twilio: TwilioSettings = Field(default_factory=TwilioSettings)


settings = Settings()
