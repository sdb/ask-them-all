from typing import Literal, Dict, Tuple, Type

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class OpenSearchSettings(BaseModel):
    host: str = Field("localhost")
    port: int = Field("9200")
    index_prefix: str = Field("askthemall_")


class GoogleSettings(BaseModel):
    api_key: str


class GroqSettings(BaseModel):
    api_key: str


class MistralSettings(BaseModel):
    api_key: str


class ClientSettings(BaseModel):
    type: Literal["google", "groq", "mistral"]
    model_name: str


class ChatBotSettings(BaseModel):
    name: str
    client: ClientSettings


class Settings(BaseSettings):
    app_name: str = "AskThemAll"
    opensearch: OpenSearchSettings
    google: GoogleSettings
    groq: GroqSettings
    mistral: MistralSettings
    chat_bots: Dict[str, ChatBotSettings]

    model_config = SettingsConfigDict(
        env_file=".env",
        toml_file=[".askthemall/config.toml", "/config/config.toml"],
        env_nested_delimiter="__",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            dotenv_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )
