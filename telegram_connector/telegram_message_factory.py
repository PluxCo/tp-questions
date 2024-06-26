"""
File with Telegram message factory implementation.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from core.answers import OpenRecord, TestRecord, Record, AnswerState
from core.routes import MessageFactory
from db_connector import DBWorker
from telegram_connector.telegram_message import TelegramOpenMessage, TelegramTestMessage, TelegramMessage, \
    TelegramReplyMessage

if TYPE_CHECKING:
    from generator.router import PersonRouter

logger = logging.getLogger(__name__)


# noinspection GrazieInspection,Style,Annotator
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

    @staticmethod
    def get_record(message_id: int) -> Record:
        r"""
        Retrieves a record from the database.

        :param message_id: (:class:`int`) The ID of the message record to retrieve.
        :return: (:class:`Record`) The retrieved record object.
        """
        with DBWorker() as db_worker:
            return db_worker.scalar(select(Record).where(Record.message_id == message_id))

    def get_message(self, message_id: int) -> TelegramMessage:
        r"""
        Retrieves a message object based on the message ID.

        :param message_id: (:class:`int`) The ID of the message to retrieve.
        :return: (:class:`Union`\[:class:`TelegramOpenMessage`, :class:`TelegramTestMessage`]) The retrieved
        message object.
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
        logger.debug("Sending messages...")

        try:
            for message in self._messages:
                message.send()
            self._messages = []
        except Exception as e:
            logger.exception(e)
        else:
            logger.debug("Messages sent")

    def response_handler(self, data: dict) -> None:
        """
        Handles incoming responses to messages.

        :param data: (:class:`dict`) The response data received.
        """
        logger.debug("Handling incoming answer...")
        try:
            message = self.get_message(data['message_id'])
            logger.debug(f"Received message: {data}")

            message.handle_answer(data)
        except Exception as e:
            logger.exception(e)
            raise e
        else:
            logger.debug("Answer handled")

    def request_delivery(self, user_id: str) -> None:
        """
        Requests delivery of a message to a specific user.

        :param user_id: (:class:`int`) The ID of the user to deliver the message to.
        """
        logger.debug("Requesting delivery...")
        try:
            # FIXME: Please get rid of this in the future because it is some shitty shit / eccentric temporary solution
            with DBWorker() as db_worker:
                old_question = db_worker.scalar(select(Record).where(Record.person_id == user_id,
                                                                     Record.state == AnswerState.TRANSFERRED))
                if old_question is not None:
                    self._messages.append(TelegramReplyMessage(old_question))
                else:
                    self._router.prepare_next(user_id, db_worker)
            self.send_messages()
        except Exception as e:
            logger.exception(e)
        else:
            logger.debug("Delivery requested")

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
        """
        Gets the TelegramMessage object for this factory
        :return: (:class: `TelegramMessage`) The TelegramMessage object representing the message.
        """
        return self._message

    def create_test(self, record: TestRecord) -> None:
        self._message = TelegramTestMessage(record)

    def create_open(self, record: OpenRecord) -> None:
        self._message = TelegramOpenMessage(record)
