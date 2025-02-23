from unittest.mock import patch, MagicMock

import pytest

from askthemall.core.client import ChatInteraction
from askthemall.lc import LangChainClient, LangChainSession


@pytest.fixture
def some_interaction_model():
    return ChatInteraction(
        question="some_question",
        answer="some_answer",
    )


@pytest.fixture
def client():
    return LangChainClient(
        llm_type="some_llm_type",
        api_key="some_api_key",
        client_id="some_id",
        model_name="some_model_name",
        name="Some name"
    )


@pytest.fixture
def memory_mock():
    with patch("askthemall.lc.ConversationBufferMemory") as MockConversationBufferMemory:
        mock_instance = MagicMock()
        MockConversationBufferMemory.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def llm_factory_mock():
    with patch("askthemall.lc.create_llm") as llm_factory_mock:
        yield llm_factory_mock


@pytest.fixture
def llm_mock(llm_factory_mock):
    chat_model = MagicMock()
    llm_factory_mock.return_value = chat_model
    return chat_model


@pytest.fixture
def conversation_chain_class_mock():
    with patch("askthemall.lc.ConversationChain") as conversation_chain_class_mock:
        yield conversation_chain_class_mock


@pytest.fixture
def conversation_chain_mock(conversation_chain_class_mock):
    conversation_chain = MagicMock()
    conversation_chain_class_mock.return_value = conversation_chain
    return conversation_chain


@pytest.fixture
def session(llm_mock, memory_mock, conversation_chain_mock):
    return LangChainSession(llm_mock)


def test_client_id_property(client):
    assert client.id == "some_id"


def test_client_name_property(client):
    assert client.name == "Some name"


def test_client_start_session(client, memory_mock, llm_factory_mock, llm_mock, conversation_chain_class_mock):
    session = client.start_session()

    assert isinstance(session, LangChainSession)
    memory_mock.save_context.assert_not_called()
    conversation_chain_class_mock.assert_called_once_with(
        llm=llm_mock,
        memory=memory_mock)
    llm_factory_mock.assert_called_once_with(
        "some_llm_type",
        "some_model_name",
        "some_api_key")


def test_client_restore_session_empty_history(client, memory_mock, llm_factory_mock, llm_mock,
                                              conversation_chain_class_mock):
    session = client.restore_session([])

    assert isinstance(session, LangChainSession)
    memory_mock.save_context.assert_not_called()
    conversation_chain_class_mock.assert_called_once_with(
        llm=llm_mock,
        memory=memory_mock)
    llm_factory_mock.assert_called_once_with(
        "some_llm_type",
        "some_model_name",
        "some_api_key")


def test_client_restore_session_with_history(client, some_interaction_model, memory_mock, llm_factory_mock, llm_mock,
                                             conversation_chain_class_mock):
    session = client.restore_session([some_interaction_model])

    assert isinstance(session, LangChainSession)
    memory_mock.save_context.assert_called_once_with(
        {"input": some_interaction_model.question},
        {"output": some_interaction_model.answer})
    conversation_chain_class_mock.assert_called_once_with(
        llm=llm_mock,
        memory=memory_mock)
    llm_factory_mock.assert_called_once_with(
        "some_llm_type",
        "some_model_name",
        "some_api_key")


def test_ask_question(session, memory_mock, conversation_chain_mock):
    conversation_chain_mock.predict.return_value = "some_answer"
    answer = session.ask("some_question")
    conversation_chain_mock.predict.assert_called_once_with(input="some_question")
    assert answer == "some_answer"
