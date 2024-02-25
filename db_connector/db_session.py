"""
file that describes a database initialization and connectivity
"""

from typing import Callable, Optional

import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = dec.declarative_base()

# Global variable to store the SQLAlchemy session factory
__factory: Optional[Callable] = None


def global_init(db_file: str, modules_initializer: Optional[Callable], drop_db=False):
    """
    Initialize the global SQLAlchemy session factory and create or drop/create database tables.

    :param db_file: The path to the SQLite database file.
    :param modules_initializer: Function to initialize and create models
    :param drop_db: Whether to drop and recreate the database tables.
    :return: None

    :raises Exception: If the database file is not provided.
    """

    global __factory

    if __factory and not drop_db:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # Create a connection string for SQLite
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    # Create an SQLAlchemy engine and session factory
    engine = sa.create_engine(conn_str, echo=False)

    if drop_db:
        # Drop all tables if specified
        SqlAlchemyBase.metadata.drop_all(engine)

    modules_initializer()

    # Create database tables if they don't exist
    SqlAlchemyBase.metadata.create_all(engine)

    __factory = orm.sessionmaker(bind=engine)


def create_session() -> Session:
    """
    Create a new SQLAlchemy session.

    :return: A new SQLAlchemy session.
    :rtype: Session

    :raises AttributeError: If the session factory is not initialized.
    """

    # Ensure the session factory is initialized
    if __factory is None:
        raise AttributeError("Session factory is not initialized.")

    # Create and return a new session
    return __factory()
