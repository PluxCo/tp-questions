from __future__ import annotations

from typing import Union, TYPE_CHECKING

from sqlalchemy import select

from core.answers import OpenRecord, TestRecord, Record
from core.routes import MessageFactory
from db_connector import DBWorker
from telegram_connector.telegram_message import TelegramOpenMessage, TelegramTestMessage, TelegramMessage

if TYPE_CHECKING:
    from generator.router import PersonRouter


class TelegramMessageFactory(MessageFactory):
    """
    Represents a factory for creating Telegram messages.
    """

    def __init__(self, router: PersonRouter):
        """
        Initializes a TelegramMessageFactory object.

        This constructor initializes the message dictionary and router.
        """
        super().__init__()
        self._messages = []
        self._router = router

    def get_record(self, message_id: int) -> Union[OpenRecord, TestRecord]:
        r"""
        Retrieves a record from the database.

        :param message_id: (:class:`int`) The ID of the message record to retrieve.
        :return: (:class:`Union`\[:class:`OpenRecord`, :class:`TestRecord`]) The retrieved record object.
        """
        with DBWorker() as db_worker:
            return db_worker.scalar(select(Record).where(Record.message_id == message_id))

    def get_message(self, message_id: int) -> TelegramMessage:
        r"""
        Retrieves a message object based on the message ID.

        :param message_id: (:class:`int`) The ID of the message to retrieve.
        :return: (:class:`Union`\[:class:`TelegramOpenMessage`, :class:`TelegramTestMessage`]) The retrieved message object.
        """
        record = self.get_record(message_id)
        proxy_message = ProxyMessageFactory()
        record.dispatch(proxy_message)
        return proxy_message.get_message()

    def send_messages(self) -> None:
        """
        Sends all messages stored in the factory.

        This method iterates through all stored messages and sends each one.
        After sending, it clears the stored messages' dictionary.
        """
        for message in self._messages:
            message.send()
        self._messages = []

    def response_handler(self, data: dict) -> None:
        """
        Handles incoming responses to messages.

        :param data: (:class:`dict`) The response data received.
        """
        message = self.get_message(data['answer']["reply_to"])
        message.handle_answer(data["answer"]['data'])

    def request_delivery(self, user_id: str) -> None:
        """
        Requests delivery of a message to a specific user.

        :param user_id: (:class:`int`) The ID of the user to deliver the message to.
        """
        self._router.prepare_next(user_id)
        self.send_messages()

    def create_open(self, record: OpenRecord) -> None:
        """
        Creates a TelegramOpenMessage from an OpenRecord.

        :param record: (:class:`OpenRecord`) The OpenRecord object to create the message from.
        """
        self._messages.append(TelegramOpenMessage(record))

    def create_test(self, record: TestRecord) -> None:
        """
        Creates a TelegramTestMessage from a TestRecord.

        :param record: (:class:`TestRecord`) The TestRecord object to create the message from.
        """
        self._messages.append(TelegramTestMessage(record))


class ProxyMessageFactory(MessageFactory):
    def __init__(self):
        super().__init__()
        self._message = None

    def get_message(self) -> TelegramMessage:
        return self._message

    def create_test(self, record: TestRecord) -> None:
        self._message = TelegramTestMessage(record)

    def create_open(self, record: OpenRecord) -> None:
        self._message = TelegramOpenMessage(record)
