from typing import List

from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

from askthemall.core.client import ChatSession, ChatClient, SUGGEST_TITLE_QUESTION
from askthemall.core.persistence import InteractionData


class LangChainSession(ChatSession):

    def __init__(self, llm: BaseChatModel, history: List[InteractionData] = None):
        self.__llm = llm
        self.__memory = ConversationBufferMemory()
        if history:
            for interaction_data in history:
                self.__memory.save_context(
                    {"input": interaction_data.question},
                    {"output": interaction_data.answer})
        self.__conversation = ConversationChain(
            llm=self.__llm,
            memory=self.__memory
        )

    def __ask(self, question, remember=True) -> str:
        answer = self.__conversation.predict(input=question)
        if not remember:
            self.__memory.chat_memory.messages.pop()
            self.__memory.chat_memory.messages.pop()
        return answer

    def ask(self, question) -> str:
        return self.__ask(question)

    def suggest_title(self) -> str:
        return self.__ask(" ".join(SUGGEST_TITLE_QUESTION), remember=False).rstrip().strip('"')


class LangChainClient(ChatClient):

    def __init__(self, llm_type: str, api_key: str, client_id: str, model_name: str, name: str):
        self.__api_key = api_key
        self.__id = client_id
        self.__model_name = model_name
        self.__name = name
        self.__llm_type = llm_type

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    def __create_llm(self) -> BaseChatModel:
        match self.__llm_type:
            case "mistral":
                # noinspection PyTypeChecker
                return ChatMistralAI(model=self.__model_name, mistral_api_key=self.__api_key)
            case "google":
                # noinspection PyTypeChecker
                return ChatGoogleGenerativeAI(model=self.__model_name, google_api_key=self.__api_key)
            case "groq":
                # noinspection PyTypeChecker,PyArgumentList
                return ChatGroq(model=self.__model_name, groq_api_key=self.__api_key)

    def start_session(self) -> LangChainSession:
        return LangChainSession(self.__create_llm())

    def restore_session(self, interaction_data_list: List[InteractionData]) -> LangChainSession:
        return LangChainSession(self.__create_llm(), history=interaction_data_list)
