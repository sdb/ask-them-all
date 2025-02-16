from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, List


@dataclass
class InteractionData:
    id: str
    question: str
    answer: str
    asked_at: datetime
    chat_id: str

    def __post_init__(self):
        if isinstance(self.asked_at, str):
            self.asked_at = datetime.fromisoformat(self.asked_at)


@dataclass
class ChatData:
    id: str
    slug: str
    title: str
    created_at: datetime
    chat_bot_id: str

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.asked_at = datetime.fromisoformat(self.created_at)


@dataclass
class ChatBotData:
    id: str
    name: str


Data = TypeVar('Data')


class DataListResult(Generic[Data]):

    def __init__(self, data: List[Data], total_results):
        self.__data = data
        self.__total_results = total_results

    @property
    def data(self) -> List[Data]:
        return self.__data

    @property
    def total_results(self) -> int:
        return self.__total_results


class DatabaseClient(ABC):

    @abstractmethod
    def save_chat(self, chat: ChatData):
        pass

    @abstractmethod
    def get_chat_by_id(self, chat_id) -> ChatData:
        pass

    @abstractmethod
    def save_interaction(self, interaction: InteractionData):
        pass

    @abstractmethod
    def list_all_chats(self, chat_bot_id, max_results=100) -> DataListResult[ChatData]:
        pass

    @abstractmethod
    def list_all_interactions(self, chat_id) -> list[InteractionData]:
        pass

    @abstractmethod
    def list_all_chat_bots(self) -> List[ChatBotData]:
        pass

    @abstractmethod
    def delete_chat(self, chat_id):
        pass

    @abstractmethod
    def delete_interactions(self, chat_id):
        pass

    @abstractmethod
    def save_chat_bot(self, chat_bot: ChatBotData):
        pass

    @abstractmethod
    def migrate(self):
        pass
