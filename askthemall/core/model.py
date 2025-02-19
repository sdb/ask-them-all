from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from boltons.strutils import slugify

from askthemall.core.client import ChatClient
from askthemall.core.persistence import ChatData, InteractionData, DatabaseClient, ChatBotData


@dataclass
class Interaction:
    id: str
    chat_id: str
    question: str
    answer: str
    asked_at: datetime

    def get_data(self):
        return InteractionData(
            id=self.id,
            chat_id=self.chat_id,
            question=self.question,
            answer=self.answer,
            asked_at=self.asked_at
        )

    @classmethod
    def from_data(cls, interaction_data: InteractionData):
        return cls(
            id=interaction_data.id,
            chat_id=interaction_data.chat_id,
            question=interaction_data.question,
            answer=interaction_data.answer,
            asked_at=interaction_data.asked_at
        )


class ChatModel:

    def __init__(self, chat_bot: ChatBotModel, database_client: DatabaseClient):
        self.created_at = datetime.now()
        self.id = f"{chat_bot.id}-{datetime.now().timestamp()}"
        self.slug = None
        self.title = f'Chat with {chat_bot.name}'
        self.interactions: list[Interaction] = []
        self.started = False
        self.__session = None
        self.__chat_bot = chat_bot
        self.__chat_client = chat_bot.chat_client
        self.__database_client = database_client

    @property
    def assistant_name(self):
        return self.__chat_bot.name

    @property
    def enabled(self) -> bool:
        return self.__chat_client is not None

    def ask_question(self, question):
        answer = self.__session.ask(question)
        asked_at = datetime.now()
        interaction = Interaction(
            id=f"{self.__chat_bot.id}-{asked_at.timestamp()}",
            chat_id=self.id,
            question=question,
            answer=answer,
            asked_at=asked_at)
        self.interactions.append(interaction)
        if not self.started:
            self.title = self.__session.suggest_title()
            self.slug = "-".join([slugify(self.title, delim='-'), str(int(datetime.now().timestamp()))])
            self.__database_client.save_chat(self.get_data())
            self.started = True
        self.__database_client.save_interaction(interaction.get_data())
        return answer

    def start_chat(self):
        self.__session = self.__chat_client.start_session()

    def restore_chat(self):
        interaction_data_list = self.__database_client.list_all_interactions(self.id)
        self.interactions = list(map(lambda i: Interaction.from_data(i), interaction_data_list))
        if self.__chat_client:
            self.__session = self.__chat_client.restore_session(interaction_data_list)

    def remove(self):
        self.__database_client.delete_chat(self.id)
        self.__database_client.delete_interactions(self.id)

    def get_data(self) -> ChatData:
        return ChatData(
            id=self.id,
            chat_bot_id=self.__chat_bot.id,
            slug=self.slug,
            title=self.title,
            created_at=self.created_at
        )

    @classmethod
    def from_data(cls, chat_bot: ChatBotModel, chat_data: ChatData, database_client: DatabaseClient):
        chat = cls(chat_bot, database_client)
        chat.id = chat_data.id
        chat.slug = chat_data.slug
        chat.title = chat_data.title
        chat.created_at = chat_data.created_at
        chat.started = True
        return chat


class ChatListModel:

    def __init__(self, chats: List[ChatModel], total_results: int):
        self.chats = chats
        self.total_results = total_results


class ChatBotModel:

    def __init__(self, chat_bot_id: str, name: str, chat_client: ChatClient, database_client: DatabaseClient):
        self.__chat_client = chat_client
        self.__database_client = database_client
        self.__id = chat_bot_id
        self.__name = name

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def chat_client(self) -> ChatClient:
        return self.__chat_client

    @property
    def enabled(self) -> bool:
        return self.__chat_client is not None

    def get_chat(self, chat_id: str) -> ChatModel:
        chat_data = self.__database_client.get_chat_by_id(chat_id)
        return ChatModel.from_data(self, chat_data, self.__database_client)

    def get_all_chats(self, max_results: int = 100) -> ChatListModel:
        chat_data_list_result = self.__database_client.list_all_chats(self.id, max_results=max_results)
        return ChatListModel(
            chats=list(map(lambda c: ChatModel.from_data(self, c, self.__database_client),
                           chat_data_list_result.data)),
            total_results=chat_data_list_result.total_results
        )

    def new_chat(self) -> ChatModel:
        chat = ChatModel(self, self.__database_client)
        chat.start_chat()
        return chat

    @classmethod
    def from_data(cls, chat_bot_data: ChatBotData, database_client: DatabaseClient, chat_client: ChatClient = None):
        chat_bot = cls(chat_bot_data.id, chat_bot_data.name, chat_client, database_client)
        return chat_bot


class AskThemAllModel:

    def __init__(self, database_client: DatabaseClient, chat_clients: List[ChatClient]):
        self.__chat_clients = chat_clients
        self.__database_client = database_client
        for chat_client in self.__chat_clients:
            self.__database_client.save_chat_bot(ChatBotData(
                id=chat_client.id,
                name=chat_client.name
            ))

    def __get_chat_client_by_id(self, chat_client_id: str) -> ChatClient | None:
        for chat_client in self.__chat_clients:
            if chat_client.id == chat_client_id:
                return chat_client
        return None

    def __get_chat_bot_by_id(self, chat_bot_id: str) -> ChatBotModel:
        for chat_bot_data in self.__database_client.list_all_chat_bots():
            if chat_bot_data.id == chat_bot_id:
                return ChatBotModel.from_data(chat_bot_data, self.__database_client,
                                              self.__get_chat_client_by_id(chat_bot_data.id))

    @property
    def chat_bots(self) -> List[ChatBotModel]:
        chat_bots = []
        for chat_bot_data in self.__database_client.list_all_chat_bots():
            matched_client = None
            for chat_client in self.__chat_clients:
                if chat_bot_data.id == chat_client.id:
                    matched_client = chat_client
            chat_bots.append(ChatBotModel.from_data(chat_bot_data, self.__database_client, matched_client))
        chat_bots.sort(key=lambda c: str(not c.enabled) + c.name, reverse=False)
        return chat_bots

    def filter_chats(self, search_filter: str, max_results: int = 100) -> ChatListModel:
        chat_data_list_result = self.__database_client.filter_chats(search_filter, max_results)
        return ChatListModel(
            chats=list(map(lambda c: ChatModel.from_data(self.__get_chat_bot_by_id(c.chat_bot_id), c,
                                                         self.__database_client),
                           chat_data_list_result.data)),
            total_results=chat_data_list_result.total_results
        )

    def switch_chat(self, chat_id) -> ChatModel:
        chat_data = self.__database_client.get_chat_by_id(chat_id)
        chat = ChatModel.from_data(self.__get_chat_bot_by_id(chat_data.chat_bot_id), chat_data, self.__database_client)
        chat.restore_chat()
        return chat
