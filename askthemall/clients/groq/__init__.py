from typing import List

from groq import Groq

from askthemall.core.client import ChatSession, SUGGEST_TITLE_QUESTION, ChatClient
from askthemall.core.persistence import InteractionData


class GroqSession(ChatSession):

    def __init__(self, api_key, model_name, interaction_data_list: List[InteractionData] = None):
        self.__client = Groq(api_key=api_key)
        self.__model_name = model_name
        self.__history = []
        if interaction_data_list:
            for interaction_data in interaction_data_list:
                self.__history.append({"role": "user", "content": interaction_data.question})
                self.__history.append({"role": "assistant", "content": interaction_data.answer})

    def __ask(self, question, remember=True) -> str:
        question_message = {"role": "user", "content": question}
        chat_completion = self.__client.chat.completions.create(
            model=self.__model_name,
            messages=self.__history[:] + [question_message]
        )
        response = chat_completion.choices[0].message.content
        if remember:
            self.__history.append(question_message)
            self.__history.append({"role": "assistant", "content": response})
        return response

    def ask(self, question) -> str:
        return self.__ask(question)

    def suggest_title(self) -> str:
        return self.__ask(" ".join(SUGGEST_TITLE_QUESTION), remember=False).rstrip().strip('"')


class GroqClient(ChatClient):

    def __init__(self, api_key, client_id, model_name, name: str = None):
        self.__id = client_id
        self.__model_name = model_name
        self.__api_key = api_key
        self.__name = name if name else f'Groq ({self.__model_name})'

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    def start_session(self) -> ChatSession:
        return GroqSession(api_key=self.__api_key, model_name=self.__model_name)

    def restore_session(self, interaction_data_list: List[InteractionData]) -> ChatSession:
        return GroqSession(
            api_key=self.__api_key,
            model_name=self.__model_name,
            interaction_data_list=interaction_data_list
        )
