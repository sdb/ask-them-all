from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, List


@dataclass
class Data:
    id: str


@dataclass
class InteractionData(Data):
    question: str
    answer: str
    asked_at: datetime
    chat_id: str

    def __post_init__(self):
        if isinstance(self.asked_at, str):
            self.asked_at = datetime.fromisoformat(self.asked_at)


@dataclass
class ChatData(Data):
    slug: str
    title: str
    created_at: datetime
    chat_bot_id: str

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.asked_at = datetime.fromisoformat(self.created_at)


@dataclass
class ChatBotData(Data):
    name: str


D = TypeVar("D", bound=Data)


class DataListResult(Generic[D]):
    def __init__(self, data: List[D], total_results):
        self.__data = data
        self.__total_results = total_results

    @property
    def data(self) -> List[D]:
        return self.__data

    @property
    def total_results(self) -> int:
        return self.__total_results


class Repository(ABC, Generic[D]):
    @abstractmethod
    def save(self, data: D):
        pass

    @abstractmethod
    def get_by_id(self, data_id) -> D:
        pass

    @abstractmethod
    def find_all(self) -> list[D]:
        pass

    @abstractmethod
    def delete_by_id(self, data_id):
        pass


class ChatRepository(Repository[ChatData], ABC):
    @abstractmethod
    def find_all_by_chat_bot_id(
        self, chat_bot_id, max_results
    ) -> DataListResult[ChatData]:
        pass

    @abstractmethod
    def search_chats(
        self, search_filter: str, max_results=100
    ) -> DataListResult[ChatData]:
        pass


class ChatBotRepository(Repository[ChatBotData], ABC):
    pass


class InteractionRepository(Repository[InteractionData], ABC):
    pass

    @abstractmethod
    def find_all_by_chat_id(self, chat_id: str) -> list[InteractionData]:
        pass

    @abstractmethod
    def delete_all_by_chat_id(self, chat_id):
        pass


class DatabaseMigration(ABC):
    @abstractmethod
    def migrate(self):
        pass
