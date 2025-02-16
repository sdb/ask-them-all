from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import streamlit as st

from askthemall.core.model import ChatModel, ChatBotModel, AskThemAllModel
from askthemall.view.helpers import ScrollIntoView


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

    def __init__(self, chat: ChatModel,
                 chat_hub_listener: ChatHubViewModelListener):
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


class ChatListViewModel:

    def __init__(self, chat_bot: ChatBotModel,
                 chat_hub_listener: ChatHubViewModelListener):
        self.__chat_hub_listener = chat_hub_listener
        self.__chat_bot = chat_bot
        max_results = st.session_state.chat_bots_config[chat_bot.id]['max_results']
        chat_list = chat_bot.get_all_chats(max_results=max_results)
        self.__total_results = chat_list.total_results
        self.__chats = chat_list.chats

    @property
    def chat_bot_id(self) -> str:
        return self.__chat_bot.id

    @property
    def title(self) -> str:
        return self.__chat_bot.name

    @property
    def chats(self) -> list[ChatListItemViewModel]:
        return list(map(lambda c: ChatListItemViewModel(c, self.__chat_hub_listener), self.__chats))

    @property
    def total_results(self) -> int:
        return self.__total_results

    @property
    def new_chat_enabled(self):
        return self.__chat_bot.enabled

    @property
    def has_more_chats(self):
        return self.total_results > len(self.chats)

    def new_chat(self):
        chat = self.__chat_bot.new_chat()
        self.__chat_hub_listener.on_new_chat_started(chat)

    def switch_chat(self, chat_id: str):
        chat = self.__chat_bot.switch_chat(chat_id)
        self.__chat_hub_listener.on_chat_switched(chat)
        st.rerun()

    def load_more_chats(self):
        st.session_state.chat_bots_config[self.chat_bot_id]['max_results'] += 5
        st.rerun()


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

    def __init__(self, chat: ChatModel,
                 chat_hub_listener: ChatHubViewModelListener):
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
        return list(map(lambda i: ChatInteractionViewModel(
            interaction_id=i.id,
            question=i.question,
            answer=i.answer,
            asked_at=i.asked_at
        ), self.__chat.interactions))

    def ask_question(self, question):
        self.__chat.ask_question(question)
        self.__chat_hub_listener.on_question_answered(self.__chat)
        st.rerun()

    def goto_interaction(self, interaction):
        self.__chat_hub_listener.on_goto_interaction(interaction.interaction_id)
        st.rerun()


class AskThemAllViewModel(ChatHubViewModelListener):

    def __init__(self, app_title: str, ask_them_all_model: AskThemAllModel):
        self.__app_title = app_title
        self.__ask_them_all_model = ask_them_all_model
        self.__chat_bots = ask_them_all_model.chat_bots
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.chat_bots_config = {}
            for chat_client in self.__chat_bots:
                config = {
                    'max_results': 5
                }
                st.session_state.chat_bots_config[chat_client.id] = config

    @property
    def __chat(self):
        return st.session_state.chat if 'chat' in st.session_state else None

    @__chat.setter
    def __chat(self, chat):
        st.session_state.chat = chat

    @property
    def __scroll_to(self):
        return st.session_state.scroll_to if 'scroll_to' in st.session_state else None

    @__scroll_to.setter
    def __scroll_to(self, to):
        st.session_state.scroll_to = to

    @property
    def app_title(self):
        return self.__app_title

    @property
    def chat_lists(self):
        chat_lists = []
        for chat_bot in self.__chat_bots:
            chat_list = ChatListViewModel(
                chat_bot=chat_bot,
                chat_hub_listener=self
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
            id=chat.interactions[-1].id,
            behavior='instant'
        )

    def on_question_answered(self, chat: ChatModel):
        self.__scroll_to = ScrollIntoView(
            id=chat.interactions[-1].id,
            behavior='instant'
        )

    def on_goto_interaction(self, interaction_id: str):
        self.__scroll_to = ScrollIntoView(
            id=interaction_id,
            behavior='smooth',
            delay=100
        )
