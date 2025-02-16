from typing import List

from google import generativeai as genai
from google.generativeai import ChatSession as GenaiChatSession
from google.generativeai.types import PartDict, ContentDict

from askthemall.core.client import ChatSession, SUGGEST_TITLE_QUESTION, ChatClient
from askthemall.core.persistence import InteractionData


class GeminiSession(ChatSession):

    def __init__(self, model, interaction_data_list: List[InteractionData] = None):
        def create_parts(text):
            # noinspection PyArgumentList
            return [PartDict(text=text)]

        history = []
        if interaction_data_list:
            for interaction_data in interaction_data_list:
                question = ContentDict(role='user', parts=create_parts(interaction_data.question))
                history.append(question)
                answer = ContentDict(role='model', parts=create_parts(text=interaction_data.answer))
                history.append(answer)
        self.__chat_session = GenaiChatSession(model=model, history=history)

    def __ask(self, question, remember=True) -> str:
        answer = self.__chat_session.send_message(question).text
        if not remember:
            self.__chat_session.rewind()
        return answer

    def ask(self, question) -> str:
        return self.__ask(question)

    def suggest_title(self) -> str:
        return self.__ask(" ".join(SUGGEST_TITLE_QUESTION), remember=False).rstrip()


class GeminiClient(ChatClient):

    def __init__(self, client_id, model_name, name: str = None):
        self.__id = client_id
        self.__model_name = model_name
        self.__name = name if name else f'Gemini ({self.__model_name})'
        self.__model = genai.GenerativeModel(self.__model_name)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    def start_session(self) -> ChatSession:
        return GeminiSession(model=self.__model)

    def restore_session(self, interaction_data_list: List[InteractionData]) -> ChatSession:
        return GeminiSession(
            model=self.__model,
            interaction_data_list=interaction_data_list
        )
