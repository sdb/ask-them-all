import pytest

from tests.core.persistence import ChatBotDataFactory


@pytest.fixture(autouse=True)
def test_data(opensearch, index_names):
    chat_bot_data_list = ChatBotDataFactory.create_batch(5)
    for chat_bot_data in chat_bot_data_list:
        opensearch.get_client().index(
            index=index_names.chat_bots,
            body=chat_bot_data.__dict__,
            refresh=True,
        )
    yield
    indices = ['askthemall_test_chats', 'askthemall_test_chat_bots', 'askthemall_test_interactions']
    for index_name in indices:
        opensearch.get_client().delete_by_query(index=index_name, body={
            "query": {
                "match_all": {}
            }
        })
    opensearch.get_client().indices.refresh()


def test_find_all(chat_bot_repository):
    chat_bots = chat_bot_repository.find_all()
    assert len(chat_bots) == 5
