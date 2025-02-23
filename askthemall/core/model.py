from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from boltons.strutils import slugify
from dependency_injector.wiring import inject, Provide

from askthemall.core.client import ChatClient, ChatInteraction
from askthemall.core.persistence import (ChatData,
                                         InteractionData,
                                         ChatBotData,
                                         ChatRepository,
                                         InteractionRepository,
                                         ChatBotRepository)


@dataclass
class InteractionModel:
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

    @inject
    def __init__(self,
                 chat_bot: ChatBotModel,
                 chat_repository: ChatRepository = Provide["chat_repository"],
                 interaction_repository: InteractionRepository = Provide["interaction_repository"]):
        self.created_at = datetime.now()
        self.id = f"{chat_bot.id}-{datetime.now().timestamp()}"
        self.slug = None
        self.title = f'Chat with {chat_bot.name}'
        self.interactions: list[InteractionModel] = []
        self.started = False
        self.__session = None
        self.__chat_bot = chat_bot
        self.__chat_client = chat_bot.chat_client
        self.__chat_repository = chat_repository
        self.__interaction_repository = interaction_repository

    @property
    def assistant_name(self):
        return self.__chat_bot.name

    @property
    def enabled(self) -> bool:
        return self.__chat_client is not None

    def ask_question(self, question):
        answer = self.__session.ask(question)
        asked_at = datetime.now()
        interaction = InteractionModel(
            id=f"{self.__chat_bot.id}-{asked_at.timestamp()}",
            chat_id=self.id,
            question=question,
            answer=answer,
            asked_at=asked_at)
        self.interactions.append(interaction)
        if not self.started:
            self.title = self.__session.suggest_title()
            self.slug = "-".join([slugify(self.title, delim='-'), str(int(datetime.now().timestamp()))])
            self.__chat_repository.save(self.get_data())
            self.started = True
        self.__interaction_repository.save(interaction.get_data())
        return answer

    def start_chat(self):
        self.__session = self.__chat_client.start_session()

    def restore_chat(self):
        interaction_data_list = self.__interaction_repository.find_all_by_chat_id(self.id)
        self.interactions = list(map(lambda i: InteractionModel.from_data(i), interaction_data_list))
        if self.__chat_client:
            self.__session = self.__chat_client.restore_session(list(map(lambda i: ChatInteraction(
                question=i.question,
                answer=i.answer
            ), self.interactions)))

    def remove(self):
        self.__chat_repository.delete_by_id(self.id)
        self.__interaction_repository.delete_all_by_chat_id(self.id)

    def get_data(self) -> ChatData:
        return ChatData(
            id=self.id,
            chat_bot_id=self.__chat_bot.id,
            slug=self.slug,
            title=self.title,
            created_at=self.created_at
        )

    @classmethod
    def from_data(cls,
                  chat_bot: ChatBotModel,
                  chat_data: ChatData):
        chat = cls(chat_bot)
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

    @inject
    def __init__(self,
                 chat_bot_id: str,
                 name: str,
                 chat_client: ChatClient,
                 chat_repository: ChatRepository = Provide["chat_repository"]):
        self.__chat_client = chat_client
        self.__chat_repository = chat_repository
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
        chat_data = self.__chat_repository.get_by_id(chat_id)
        return ChatModel.from_data(self, chat_data)

    def get_all_chats(self, max_results: int = 100) -> ChatListModel:
        chat_data_list_result = self.__chat_repository.find_all_by_chat_bot_id(self.id, max_results=max_results)
        return ChatListModel(
            chats=list(
                map(lambda c: ChatModel.from_data(self, c),
                    chat_data_list_result.data)),
            total_results=chat_data_list_result.total_results
        )

    def new_chat(self) -> ChatModel:
        chat = ChatModel(self)
        chat.start_chat()
        return chat

    @classmethod
    def from_data(cls, chat_bot_data: ChatBotData, chat_client: ChatClient = None):
        chat_bot = cls(chat_bot_data.id, chat_bot_data.name, chat_client)
        return chat_bot


class AskThemAllModel:

    @inject
    def __init__(self,
                 chat_bot_repository: ChatBotRepository = Provide["chat_bot_repository"],
                 chat_repository: ChatRepository = Provide["chat_repository"],
                 chat_clients: List[ChatClient] = Provide["chat_clients"]):
        self.__chat_clients = chat_clients
        self.__chat_bot_repository = chat_bot_repository
        self.__chat_repository = chat_repository
        for chat_client in self.__chat_clients:
            self.__chat_bot_repository.save(ChatBotData(
                id=chat_client.id,
                name=chat_client.name
            ))

    def __get_chat_client_by_id(self, chat_client_id: str) -> ChatClient | None:
        for chat_client in self.__chat_clients:
            if chat_client.id == chat_client_id:
                return chat_client
        return None

    def __get_chat_bot_by_id(self, chat_bot_id: str) -> ChatBotModel:
        for chat_bot_data in self.__chat_bot_repository.find_all():
            if chat_bot_data.id == chat_bot_id:
                return ChatBotModel.from_data(chat_bot_data, self.__get_chat_client_by_id(chat_bot_data.id))

    @property
    def chat_bots(self) -> List[ChatBotModel]:
        chat_bots = []
        for chat_bot_data in self.__chat_bot_repository.find_all():
            matched_client = None
            for chat_client in self.__chat_clients:
                if chat_bot_data.id == chat_client.id:
                    matched_client = chat_client
            chat_bots.append(ChatBotModel.from_data(chat_bot_data, matched_client))
        chat_bots.sort(key=lambda c: str(not c.enabled) + c.name, reverse=False)
        return chat_bots

    def filter_chats(self, search_filter: str, max_results: int = 100) -> ChatListModel:
        chat_data_list_result = self.__chat_repository.search_chats(search_filter, max_results)
        return ChatListModel(
            chats=list(map(lambda c: ChatModel.from_data(self.__get_chat_bot_by_id(c.chat_bot_id), c),
                           chat_data_list_result.data)),
            total_results=chat_data_list_result.total_results
        )

    def switch_chat(self, chat_id) -> ChatModel:
        chat_data = self.__chat_repository.get_by_id(chat_id)
        chat = ChatModel.from_data(self.__get_chat_bot_by_id(chat_data.chat_bot_id), chat_data)
        chat.restore_chat()
        return chat
