import locale
import logging

from dependency_injector.wiring import inject, Provide

from askthemall import view
from askthemall.core.persistence import DatabaseMigration


@inject
def run(database_migration: DatabaseMigration = Provide["database_migration"]):
    # TODO: skip init if application is already running to improve performance when not in dev mode

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    locale.setlocale(locale.LC_TIME, "")
    database_migration.migrate()
    view.render()
