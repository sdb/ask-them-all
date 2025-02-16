from dataclasses import dataclass

from boltons.strutils import slugify


@dataclass
class ClientConfig:
    id: str
    key: str
    type: str
    model_name: str
    name: str = None

    @classmethod
    def config(cls, client_type: str, model_name: str, client_id: str = None, key: str = None, name: str = None):
        _client_id = client_id if client_id else f"{client_type}-{model_name}"
        _key = key if key else slugify(_client_id)
        return cls(
            id=_client_id,
            key=_key,
            type=client_type,
            model_name=model_name,
            name=name if name else f'{client_type.capitalize()} ({model_name})'
        )


clients = [
    ClientConfig.config("gemini", "gemini-1.5-flash", client_id="gemini-1.5-flash"),
    ClientConfig.config("gemini", "gemini-2.0-flash-exp", client_id="gemini-2.0-flash-exp"),
    ClientConfig.config("groq", "mixtral-8x7b-32768"),
    ClientConfig.config("groq", "llama-3.3-70b-versatile"),
    ClientConfig.config("groq", "gemma2-9b-it")
]

# TODO: log client config
