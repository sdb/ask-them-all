from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import streamlit as st
from dependency_injector.wiring import inject, Provide

from askthemall.core.model import (
    ChatModel,
    ChatBotModel,
    AskThemAllModel,
    ChatListModel,
)
from askthemall.view.helpers import ScrollIntoView
from askthemall.view.settings import ViewSettings


class ChatHubViewModelListener(ABC):
    @abstractmethod
    def on_new_chat_started(self, chat: ChatModel):
        pass

    @abstractmethod
    def on_chat_switched(self, chat: ChatModel):
        pass

    @abstractmethod
    def on_chat_removed(self, chat_id: str):
        pass

    @abstractmethod
    def on_question_answered(self, chat: ChatModel):
        pass

    @abstractmethod
    def on_goto_interaction(self, interaction_id: str):
        pass


class ChatListItemViewModel:
    def __init__(self, chat: ChatModel, chat_hub_listener: ChatHubViewModelListener):
        self.__chat = chat
        self.__chat_hub_listener = chat_hub_listener

    @property
    def chat_id(self) -> str:
        return self.__chat.id

    @property
    def title(self) -> str:
        return self.__chat.title

    def remove(self):
        self.__chat.remove()
        self.__chat_hub_listener.on_chat_removed(self.chat_id)
        st.rerun()


class ChatListViewModel(ABC):
    def __init__(
        self,
        ask_them_all_model: AskThemAllModel,
        chat_hub_listener: ChatHubViewModelListener,
    ):
        self.__ask_them_all_model = ask_them_all_model
        self.__chat_hub_listener = chat_hub_listener
        if self.id not in st.session_state.chat_lists_config:
            st.session_state.chat_lists_config[self.id] = {
                "max_results": self.chats_per_page
            }
        max_results = st.session_state.chat_lists_config[self.id]["max_results"]
        chat_list = self.fetch_chats(max_results)
        self.__total_results = chat_list.total_results
        self.__chats = chat_list.chats

    @property
    def chats_per_page(self) -> int:
        return 5

    @abstractmethod
    def fetch_chats(self, max_results) -> ChatListModel:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        pass

    @property
    def expanded(self) -> bool:
        return False

    @property
    def new_chat_enabled(self) -> bool:
        return False

    def new_chat(self):
        pass

    @property
    def chats(self) -> list[ChatListItemViewModel]:
        return list(
            map(
                lambda c: ChatListItemViewModel(c, self.__chat_hub_listener),
                self.__chats,
            )
        )

    @property
    def total_results(self) -> int:
        return self.__total_results

    def switch_chat(self, chat_id: str):
        chat = self.__ask_them_all_model.switch_chat(chat_id)
        self.__chat_hub_listener.on_chat_switched(chat)
        st.rerun()

    @property
    def has_more_chats(self):
        return self.total_results > len(self.chats)

    def load_more_chats(self):
        st.session_state.chat_lists_config[self.id]["max_results"] += (
            self.chats_per_page
        )
        st.rerun()


class ChatBotViewModel(ChatListViewModel):
    def __init__(
        self,
        ask_them_all_model: AskThemAllModel,
        chat_bot: ChatBotModel,
        chat_hub_listener: ChatHubViewModelListener,
    ):
        self.__ask_them_all_model = ask_them_all_model
        self.__chat_hub_listener = chat_hub_listener
        self.__chat_bot = chat_bot
        super().__init__(ask_them_all_model, chat_hub_listener)

    def fetch_chats(self, max_results) -> ChatListModel:
        chat_list = self.__chat_bot.get_all_chats(max_results=max_results)
        return chat_list

    @property
    def id(self) -> str:
        return self.__chat_bot.id

    @property
    def icon(self) -> str:
        return (
            ":material/smart_toy:"
            if self.new_chat_enabled
            else ":material/inventory_2:"
        )

    @property
    def title(self) -> str:
        return self.__chat_bot.name

    @property
    def new_chat_enabled(self):
        return self.__chat_bot.enabled

    def new_chat(self):
        chat = self.__chat_bot.new_chat()
        self.__chat_hub_listener.on_new_chat_started(chat)


class ChatSearchResultViewModel(ChatListViewModel):
    def __init__(
        self,
        search_filter: str,
        ask_them_all_model: AskThemAllModel,
        chat_hub_listener: ChatHubViewModelListener,
    ):
        self.__ask_them_all_model = ask_them_all_model
        self.__chat_hub_listener = chat_hub_listener
        self.__search_filter = search_filter
        super().__init__(ask_them_all_model, chat_hub_listener)

    def fetch_chats(self, max_results) -> ChatListModel:
        return self.__ask_them_all_model.filter_chats(self.__search_filter, max_results)

    @property
    def title(self) -> str:
        return "Search results"

    @property
    def id(self) -> str:
        return "search-results"

    @property
    def icon(self) -> str:
        return ":material/search:"

    @property
    def expanded(self) -> bool:
        return True

    @property
    def chats_per_page(self) -> int:
        return 10


@dataclass
class ChatInteractionViewModel:
    interaction_id: str
    question: str
    answer: str
    asked_at: datetime

    @property
    def question_as_title(self):
        return self.question.splitlines()[0].strip()


class ChatViewModel:
    def __init__(self, chat: ChatModel, chat_hub_listener: ChatHubViewModelListener):
        self.__chat = chat
        self.__chat_hub_listener = chat_hub_listener

    @property
    def chat_enabled(self):
        return self.__chat.enabled

    @property
    def chat_id(self) -> str:
        return self.__chat.id

    @property
    def title(self) -> str:
        return self.__chat.title

    @property
    def slug(self) -> str:
        return self.__chat.slug

    @property
    def assistant_name(self) -> str:
        return self.__chat.assistant_name

    @property
    def interactions(self) -> list[ChatInteractionViewModel]:
        return list(
            map(
                lambda i: ChatInteractionViewModel(
                    interaction_id=i.id,
                    question=i.question,
                    answer=i.answer,
                    asked_at=i.asked_at,
                ),
                self.__chat.interactions,
            )
        )

    def ask_question(self, question):
        self.__chat.ask_question(question)
        self.__chat_hub_listener.on_question_answered(self.__chat)
        st.rerun()

    def goto_interaction(self, interaction):
        self.__chat_hub_listener.on_goto_interaction(interaction.interaction_id)


class AskThemAllViewModel(ChatHubViewModelListener):
    @inject
    def __init__(self, view_settings: ViewSettings = Provide["view_settings"]):
        self.__app_title = view_settings.app_title
        self.__ask_them_all_model = AskThemAllModel()
        self.__chat_bots = self.__ask_them_all_model.chat_bots
        self.__search_filter = None
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.chat_lists_config = {}

    @property
    def __chat(self):
        return st.session_state.chat if "chat" in st.session_state else None

    @__chat.setter
    def __chat(self, chat):
        st.session_state.chat = chat

    @property
    def __scroll_to(self):
        return st.session_state.scroll_to if "scroll_to" in st.session_state else None

    @__scroll_to.setter
    def __scroll_to(self, to):
        st.session_state.scroll_to = to

    @property
    def app_title(self):
        return self.__app_title

    @property
    def search_results(self):
        if self.__search_filter:
            return ChatSearchResultViewModel(
                search_filter=self.__search_filter,
                ask_them_all_model=self.__ask_them_all_model,
                chat_hub_listener=self,
            )
        else:
            return None

    @property
    def chat_lists(self):
        chat_lists = []
        for chat_bot in self.__chat_bots:
            chat_list = ChatBotViewModel(
                ask_them_all_model=self.__ask_them_all_model,
                chat_bot=chat_bot,
                chat_hub_listener=self,
            )
            chat_lists.append(chat_list)
        return chat_lists

    @property
    def current_chat(self):
        if self.__chat:
            return ChatViewModel(self.__chat, self)
        return None

    @property
    def scroll_to(self):
        return self.__scroll_to

    def reset_scroll_to(self):
        self.__scroll_to = None

    def on_new_chat_started(self, chat: ChatModel):
        self.__chat = chat

    def on_chat_removed(self, chat_id: str):
        if self.__chat and self.__chat.id == chat_id:
            self.__chat = None

    def on_chat_switched(self, chat: ChatModel):
        self.__chat = chat
        st.session_state.scroll_to = ScrollIntoView(
            id=chat.interactions[-1].id, behavior="instant"
        )

    def on_question_answered(self, chat: ChatModel):
        self.__scroll_to = ScrollIntoView(
            id=chat.interactions[-1].id, behavior="instant"
        )

    def on_goto_interaction(self, interaction_id: str):
        self.__scroll_to = ScrollIntoView(
            id=interaction_id, behavior="smooth", delay=100
        )

    @property
    def search_filter(self):
        return self.__search_filter

    @search_filter.setter
    def search_filter(self, search):
        self.__search_filter = search

    @staticmethod
    def reset_max_results():
        st.session_state.chat_lists_config = {}

    @search_filter.setter
    def search_filter(self, search):
        self.__search_filter = search

    def clear_search_filter(self):
        st.session_state["search-chats"] = None
        self.__search_filter = None
        self.reset_max_results()
