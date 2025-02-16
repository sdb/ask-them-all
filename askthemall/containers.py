import logging

import google.generativeai as genai
from dependency_injector import containers, providers

from askthemall.clients.gemini import GeminiClient
from askthemall.clients.groq import GroqClient
from askthemall.config import clients
from askthemall.core.model import AskThemAllModel
from askthemall.opensearch import OpenSearchDatabaseClient
from askthemall.settings import Settings
from askthemall.view.model import AskThemAllViewModel

logger = logging.getLogger(__name__)


def init():
    container = containers.DynamicContainer()
    settings = Settings()

    chat_client_providers = []
    for client_config in clients:
        client_settings = settings[client_config.key]
        if client_settings.enabled:
            logger.info(f"Client {client_config.key} is enabled")
            if client_config.type == "gemini":
                # TODO: only do this once and validate that api key exists
                genai.configure(api_key=settings.google.api_key)
                chat_client_providers.append(
                    providers.Singleton(
                        GeminiClient,
                        client_id=client_config.id,
                        model_name=client_config.model_name,
                        name=client_settings.name if client_settings.name else client_config.name
                    )
                )
            if client_config.type == "groq":
                chat_client_providers.append(
                    providers.Singleton(
                        GroqClient,
                        api_key=settings.groq.api_key,
                        client_id=client_config.id,
                        model_name=client_config.model_name,
                        name=client_settings.name if client_settings.name else client_config.name
                    )
                )
        else:
            logger.info(f"Client {client_config.key} is disabled")

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
