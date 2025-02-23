import logging

from dependency_injector import containers, providers
from opensearchpy import OpenSearch

from askthemall.lc import LangChainClient
from askthemall.opensearch import OpenSearchDatabaseMigration, OpenSearchChatBotRepository, OpenSearchChatRepository, \
    OpenSearchInteractionRepository, IndexNames
from askthemall.settings import Settings
from askthemall.view.settings import ViewSettings

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

    container.chat_clients = providers.List(*chat_client_providers)

    container.opensearch = providers.Singleton(
        OpenSearch,
        hosts=[{'host': settings.opensearch.host, 'port': settings.opensearch.port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )

    container.index_names = providers.Singleton(
        IndexNames,
        prefix=settings.opensearch.index_prefix
    )

    container.chat_bot_repository = providers.Singleton(
        OpenSearchChatBotRepository,
        client=container.opensearch,
        index_names=container.index_names
    )

    container.chat_repository = providers.Singleton(
        OpenSearchChatRepository,
        client=container.opensearch,
        index_names=container.index_names
    )

    container.interaction_repository = providers.Singleton(
        OpenSearchInteractionRepository,
        client=container.opensearch,
        index_names=container.index_names
    )

    container.database_migration = providers.Singleton(
        OpenSearchDatabaseMigration,
        chat_bot_repository=container.chat_bot_repository,
        chat_repository=container.chat_repository,
        interaction_repository=container.interaction_repository,
    )

    container.view_settings = providers.Singleton(
        ViewSettings,
        app_title=settings.app_name
    )

    container.wire(modules=[
        "askthemall.core.persistence",
        "askthemall.core.model",
        "askthemall.lc",
        "askthemall.opensearch",
        "askthemall.app",
        "askthemall.view",
        "askthemall.view.model",
    ])

    return container
