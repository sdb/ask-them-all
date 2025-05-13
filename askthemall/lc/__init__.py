from typing import List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

from askthemall.core.client import (
    ChatSession,
    ChatClient,
    SUGGEST_TITLE_QUESTION,
    ChatInteraction,
)


class LangChainSession(ChatSession):
    def __init__(self, llm: BaseChatModel, history: List[ChatInteraction] = None):
        self.__llm = llm
        self.__memory = InMemoryChatMessageHistory()
        self.__session_id = (
            "main_chat_session"  # A consistent ID for this session instance
        )

        if history:
            for interaction in history:
                self.__memory.add_user_message(interaction.question)
                self.__memory.add_ai_message(interaction.answer)

        # Define the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(
                    variable_name="history"
                ),  # For chat history from memory
                ("human", "{input}"),  # For the current user input
            ]
        )

        # Define the core LCEL chain: prompt -> llm -> string output
        core_chain = prompt | self.__llm | StrOutputParser()

        # Wrap the core chain with history management
        # RunnableWithMessageHistory expects a factory function that returns a BaseChatMessageHistory instance
        self.__chain_with_history = RunnableWithMessageHistory(
            core_chain,
            lambda session_id: self.__memory,  # This now returns a ChatMessageHistory instance
            input_messages_key="input",
            history_messages_key="history",
        )

    def ask(self, question: str):
        return self.__chain_with_history.stream(
            {"input": question},
            config={"configurable": {"session_id": self.__session_id}},
        )

    def suggest_title(self) -> str:
        answer = self.__chain_with_history.invoke(
            {"input": " ".join(SUGGEST_TITLE_QUESTION)},
            config={"configurable": {"session_id": self.__session_id}},
        )

        self.__memory.messages.pop()  # Pop AI's response (AIMessage)
        self.__memory.messages.pop()  # Pop user's input (HumanMessage)

        return answer.rstrip().strip('"')


class LangChainClient(ChatClient):
    def __init__(
        self, llm_type: str, api_key: str, client_id: str, model_name: str, name: str
    ):
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

    def start_session(self) -> LangChainSession:
        return LangChainSession(
            create_llm(self.__llm_type, self.__model_name, self.__api_key)
        )

    def restore_session(
        self, interaction_data_list: List[ChatInteraction]
    ) -> LangChainSession:
        return LangChainSession(
            create_llm(self.__llm_type, self.__model_name, self.__api_key),
            history=interaction_data_list,
        )


def create_llm(llm_type, model_name, api_key):
    match llm_type:
        case "mistral":
            return ChatMistralAI(model=model_name, mistral_api_key=api_key)
        case "google":
            return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        case "groq":
            return ChatGroq(model=model_name, groq_api_key=api_key)
