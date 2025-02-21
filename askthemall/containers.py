import logging

from dependency_injector import containers, providers

from askthemall.core.model import AskThemAllModel
from askthemall.lc import LangChainClient
from askthemall.opensearch import OpenSearchDatabaseClient
from askthemall.settings import Settings
from askthemall.view.model import AskThemAllViewModel

logger = logging.getLogger(__name__)


def init():
    container = containers.DynamicContainer()
    # noinspection PyArgumentList
    settings = Settings()

    chat_client_providers = []
    for chat_bot_id, chat_bot_settings in settings.chat_bots.items():
        api_keys = {
            "google": settings.google.api_key,
            "groq": settings.groq.api_key,
            "mistral": settings.mistral.api_key
        }
        chat_client_providers.append(
            providers.Singleton(
                LangChainClient,
                llm_type=chat_bot_settings.client.type,
                api_key=api_keys[chat_bot_settings.client.type],
                client_id=chat_bot_id,
                model_name=chat_bot_settings.client.model_name,
                name=chat_bot_settings.name
            )
        )

    container.database_client = providers.Singleton(
        OpenSearchDatabaseClient,
        host=settings.opensearch.host,
        port=settings.opensearch.port,
        index_prefix=settings.opensearch.index_prefix
    )

    container.chat_clients = providers.List(*chat_client_providers)

    container.ask_them_all_model = providers.Singleton(
        AskThemAllModel,
        database_client=container.database_client,
        chat_clients=container.chat_clients
    )

    container.chat_hub_view_model = providers.Singleton(
        AskThemAllViewModel,
        app_title=settings.app_name,
        ask_them_all_model=container.ask_them_all_model,
    )

    return container
