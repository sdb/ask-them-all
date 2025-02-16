from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OpenSearchSettings(BaseModel):
    host: str = Field("localhost")
    port: int = Field("9200")
    index_prefix: str = Field("askthemall_")


class GoogleSettings(BaseModel):
    api_key: str


class GroqSettings(BaseModel):
    api_key: str


class ClientSettings(BaseModel):
    # TODO: support optional title and id config
    enabled: bool = Field(False)
    name: str | None = Field(None)


class Settings(BaseSettings):
    app_name: str = "AskThemAll"
    opensearch: OpenSearchSettings | None = None
    google: GoogleSettings | None = None
    groq: GroqSettings | None = None
    gemini_1_5_flash: ClientSettings = ClientSettings()
    gemini_2_0_flash_exp: ClientSettings = ClientSettings()
    groq_mixtral_8x7b_32768: ClientSettings = ClientSettings()
    groq_llama_3_3_70b_versatile: ClientSettings = ClientSettings()
    groq_gemma2_9b_it: ClientSettings = ClientSettings()

    def __getitem__(self, item):
        return getattr(self, item)

    class Config:
        env_file = ".env"
        env_nested_delimiter = '__'
