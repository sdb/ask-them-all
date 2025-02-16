from abc import ABC, abstractmethod
from typing import List

from askthemall.core.persistence import InteractionData

SUGGEST_TITLE_QUESTION = [
    "Generate a short descriptive title with minimum 3 words and maximum 15 words for this chat",
    "The title should be exclusively based on the initial question.",
    "Do not let e choose an option from a list of possible titles.",
    "Do not indicate this was a query or question.",
    "It should indicate the purpose of the chat.",
    "And it should be in the language of the initial question.",
    "Your response should be a single line of text with no more than 15 words.",
    "Do not include any other text."
]


class ChatSession(ABC):

    @abstractmethod
    def ask(self, question) -> str:
        pass

    @abstractmethod
    def suggest_title(self) -> str:
        pass


class ChatClient(ABC):

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def start_session(self) -> ChatSession:
        pass

    @abstractmethod
    def restore_session(self, interaction_data_list: List[InteractionData]) -> ChatSession:
        pass
