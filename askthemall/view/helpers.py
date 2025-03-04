import locale
import logging
import os
from dataclasses import dataclass

import streamlit as st
from babel.dates import format_datetime as babel_format_datetime
from htbuilder import a, styles
from htbuilder.units import px

logger = logging.getLogger(__name__)


def hidden_anchor(name):
    """Creates a completely invisible anchor target for navigation."""
    return a(
        name=name,
        id=name,
        style=styles(
            scroll_margin_top=px(30),
            height=px(0),
            overflow="hidden",
            visibility="hidden",
        ),
    )(name)


@dataclass
class ScrollIntoView:
    id: str
    behavior: str = "smooth"
    delay: int = 1000


def js_scroll_to(scroll_to: ScrollIntoView):
    """Generates a JavaScript snippet that scrolls to the specified anchor."""
    js_code = f"""
        <script>
            function scrollToAnchor() {{
                var element = window.parent.document.getElementById('{scroll_to.id}');
                if (element) {{
                    element.scrollIntoView({{ behavior: '{scroll_to.behavior}', block: 'start' }});
                }}
            }}
            setTimeout(scrollToAnchor, {scroll_to.delay}); // Delay to ensure DOM is ready
        </script>
    """
    return js_code


def add_css_from_file(filename):
    filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, os.pardir, "css", filename
    )
    try:
        with open(filepath, "r") as f:
            css_code = f.read()
            st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.exception(f"Error: CSS file not found at {filepath}")


def format_datetime(dt):
    current_locale = "en_US"
    try:
        current_locale, encoding = locale.getlocale(locale.LC_TIME)
    except locale.Error:
        logger.exception("Error getting current locale")
    return babel_format_datetime(dt, locale=current_locale)
