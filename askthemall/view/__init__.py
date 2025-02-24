import logging

import streamlit as st
import streamlit.components.v1 as components

from askthemall.view.helpers import add_css_from_file, format_datetime, hidden_anchor, js_scroll_to, \
    ScrollIntoView
from askthemall.view.model import AskThemAllViewModel, ChatListViewModel

logger = logging.getLogger(__name__)


def render_chat_list(chat_list: ChatListViewModel):
    with st.expander(chat_list.title, icon=chat_list.icon, expanded=chat_list.expanded):
        if chat_list.new_chat_enabled:
            col1, col2, col3 = st.columns([1, 20, 2])
            with col1:
                st.markdown(':material/add:')
            with col2:
                if st.button("New chat", type='tertiary', use_container_width=True,
                             key=f'new-chat-{chat_list.id}'):
                    chat_list.new_chat()
        for chat in chat_list.chats:
            col1, col2, col3 = st.columns([1, 20, 2])
            with col1:
                st.markdown(':material/subject:')
            with col2:
                if st.button(chat.title, type='tertiary', help=chat.title, use_container_width=True,
                             key=f'view-chat-{chat.chat_id}'):
                    chat_list.switch_chat(chat.chat_id)
            with col3:
                if st.button(label='', icon=":material/delete_forever:", type='tertiary',
                             key=f'delete-chat-{chat.chat_id}'):
                    chat.remove()
        if chat_list.has_more_chats:
            col1, col2, col3 = st.columns([1, 20, 2])
            with col1:
                st.markdown(':material/keyboard_arrow_down:')
            with col2:
                if st.button("Load more", type='tertiary', use_container_width=True,
                             key=f'load-more-chats-{chat_list.id}'):
                    chat_list.load_more_chats()


def render():
    view_model = AskThemAllViewModel()

    st.set_page_config(
        page_title=view_model.app_title,
        page_icon=":material/smart_toy:",
        layout="wide",
        initial_sidebar_state="auto",
    )

    add_css_from_file("styles.css")

    with st.sidebar:
        if view_model.current_chat:
            with st.container(key='sidebar-outline'):
                st.title(':material/List: Outline')

                with st.expander('Questions', expanded=True):
                    for interaction in view_model.current_chat.interactions:
                        if st.button(interaction.question_as_title, type='tertiary', help=interaction.question_as_title,
                                     use_container_width=True,
                                     key=f'interaction-{interaction.interaction_id}'):
                            view_model.current_chat.goto_interaction(interaction)

        with st.container(key='sidebar-chats'):
            st.title(":material/Chat: Chats")

            search_col1, search_col2 = st.columns([10, 1])
            with search_col1:
                search = st.text_input("Search", value=view_model.search_filter, placeholder='Search...',
                                       key='search-chats', label_visibility='collapsed',
                                       on_change=view_model.reset_max_results)
                if search:
                    view_model.search_filter = search
            with search_col2:
                st.button(label="", icon=":material/close:", type='tertiary', key='clear-search',
                          on_click=view_model.clear_search_filter)

            if view_model.search_filter:
                render_chat_list(view_model.search_results)
            else:
                for chat_list in view_model.chat_lists:
                    render_chat_list(chat_list)

    if view_model.current_chat:
        st.title(view_model.current_chat.title)
        if view_model.current_chat.slug:
            st.caption(view_model.current_chat.slug)

        for interaction in view_model.current_chat.interactions:
            st.markdown(hidden_anchor(interaction.interaction_id), unsafe_allow_html=True)
            with st.chat_message('user', avatar=":material/face:"):
                st.write(interaction.question)
                st.caption(format_datetime(interaction.asked_at))
            with st.chat_message('assistant', avatar=":material/smart_toy:"):
                st.write(interaction.answer)

        if view_model.current_chat.chat_enabled:
            question = st.chat_input(f"Ask {view_model.current_chat.assistant_name}")

            if question:
                with st.spinner("Generating response..."):
                    view_model.current_chat.ask_question(question)

    if view_model.scroll_to:
        components.html(js_scroll_to(view_model.scroll_to), height=0)
        view_model.reset_scroll_to()  # Reset state to prevent continuous scrolling
