import locale
import logging

from dependency_injector import containers

from askthemall import containers
from askthemall import view


def run():
    # TODO: skip init if application is already running to improve performance when not in dev mode

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    locale.setlocale(locale.LC_TIME, '')
    container = containers.init()
    chat_hub_view_model = container.chat_hub_view_model()
    container.database_client().migrate()
    view.render(chat_hub_view_model)
