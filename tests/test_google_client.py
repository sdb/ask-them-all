from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from askthemall.clients.google import GoogleClient, GoogleSession
from askthemall.core.persistence import InteractionData


@pytest.fixture
def generative_model_mock():
    with patch("google.generativeai.GenerativeModel") as generative_model_class_mock:
        model_mock = MagicMock()
        generative_model_class_mock.return_value = model_mock
        yield model_mock


@pytest.fixture
def genai_chat_session_class_mock():
    with patch("askthemall.clients.google.GenaiChatSession") as chat_session_class_mock:
        yield chat_session_class_mock


@pytest.fixture
def genai_chat_session_mock(genai_chat_session_class_mock):
    genai_chat_session = MagicMock()
    genai_chat_session_class_mock.return_value = genai_chat_session
    return genai_chat_session


@pytest.fixture
def some_interaction_data():
    return InteractionData(
        id="some_interaction_id",
        question="some_question",
        answer="some_answer",
        asked_at=datetime.now(),
        chat_id="some_chat_id"
    )


def test_google_client_id_property():
    client = GoogleClient("some_id", "some_model_name")
    assert client.id == "some_id"


def test_google_client_name_property_based_on_model_name():
    client = GoogleClient("some_id", "some_model_name")
    assert client.name == "Google (some_model_name)"


def test_google_client_name_property():
    client_no_name = GoogleClient("some_id", "some_model_name", name='Some name')
    assert client_no_name.name == "Some name"


def test_google_client_start_session(genai_chat_session_class_mock, generative_model_mock):
    client = GoogleClient("some_id", "some_model_name")
    session = client.start_session()
    assert isinstance(session, GoogleSession)
    genai_chat_session_class_mock.assert_called_once_with(model=generative_model_mock, history=[])


def test_google_client_restore_session_empty_interaction_data(genai_chat_session_class_mock, generative_model_mock):
    client = GoogleClient("some_id", "some_model_name")
    session = client.restore_session([])
    assert isinstance(session, GoogleSession)
    genai_chat_session_class_mock.assert_called_once_with(model=generative_model_mock, history=[])


def test_google_client_restore_session_with_interaction_data(some_interaction_data, genai_chat_session_class_mock,
                                                             generative_model_mock):
    client = GoogleClient("some_id", "some_model_name")
    session = client.restore_session([some_interaction_data])
    assert isinstance(session, GoogleSession)
    expected_history = [
        {'parts': [{'text': some_interaction_data.question}], 'role': 'user'},
        {'parts': [{'text': some_interaction_data.answer}], 'role': 'model'}
    ]
    genai_chat_session_class_mock.assert_called_once_with(model=generative_model_mock, history=expected_history)


def test_ask_question(genai_chat_session_mock, generative_model_mock):
    content = MagicMock()
    type(content).text = PropertyMock(return_value="some_answer")
    genai_chat_session_mock.send_message = MagicMock(return_value=content)
    session = GoogleSession(None)
    answer = session.ask("some_question")
    assert answer == "some_answer"
