import pytest
from testcontainers.opensearch import OpenSearchContainer

from askthemall.opensearch import OpenSearchDatabaseMigration, OpenSearchChatBotRepository, OpenSearchChatRepository, \
    OpenSearchInteractionRepository, IndexNames


@pytest.fixture(scope="session")
def opensearch():
    opensearch_container = OpenSearchContainer(image='opensearchproject/opensearch:2.17.1') \
        .with_env("DISABLE_SECURITY_PLUGIN", "true") \
        .with_bind_ports(container=9200, host=9201) \
        .with_bind_ports(container=9600, host=9601)
    del opensearch_container.env['plugins.security.disabled']

    with opensearch_container as container:
        yield container


@pytest.fixture(scope="session")
def client(opensearch):
    return opensearch.get_client()


@pytest.fixture(scope="session")
def index_names():
    return IndexNames(prefix='askthemall_test_')


@pytest.fixture(scope="session")
def chat_bot_repository(client, index_names):
    return OpenSearchChatBotRepository(client, index_names)


@pytest.fixture(scope="session")
def interaction_repository(client, index_names):
    return OpenSearchInteractionRepository(client, index_names)


@pytest.fixture(scope="session")
def chat_repository(client, index_names):
    return OpenSearchChatRepository(client, index_names)


@pytest.fixture(scope="session", autouse=True)
def migration(chat_bot_repository, chat_repository, interaction_repository):
    client = OpenSearchDatabaseMigration(
        chat_bot_repository=chat_bot_repository,
        chat_repository=chat_repository,
        interaction_repository=interaction_repository
    )
    client.migrate()
    yield client
