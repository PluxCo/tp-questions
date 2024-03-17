from typing import Union

from sqlalchemy import select

from core.answers import OpenRecord, TestRecord, Record
from core.questions import OpenQuestion, TestQuestion
from core.routes import MessageFactory
from db_connector import DBWorker
from generator.generators import SmartGenerator
from generator.router import PersonRouter
from telegram_connector.TelegramMessage import TelegramOpenMessage, TelegramTestMessage


class TelegramMessageFactory(MessageFactory):
    """
    Represents a factory for creating Telegram messages.
    """

    def __init__(self):
        """
        Initializes a TelegramMessageFactory object.

        This constructor initializes the message dictionary and router.
        """
        super().__init__()
        self._messages = {}
        self._router = PersonRouter(SmartGenerator())

    def get_record(self, message_id: int) -> Union[OpenRecord, TestRecord]:
        r"""
        Retrieves a record from the database.

        :param message_id: (:class:`int`) The ID of the message record to retrieve.
        :return: (:class:`Union`\[:class:`OpenRecord`, :class:`TestRecord`]) The retrieved record object.
        """
        with DBWorker() as db_worker:
            return db_worker.scalar(select(Record).where(Record.message_id == message_id))

    def get_message(self, message_id: int) -> Union[TelegramOpenMessage, TelegramTestMessage]:
        r"""
        Retrieves a message object based on the message ID.

        :param message_id: (:class:`int`) The ID of the message to retrieve.
        :return: (:class:`Union`\[:class:`TelegramOpenMessage`, :class:`TelegramTestMessage`]) The retrieved message object.
        """
        if message_id in self._messages.keys():
            return self._messages[message_id]
        else:
            record = self.get_record(message_id)
            match record:
                case OpenRecord():
                    message = TelegramOpenMessage(record)
                case TestRecord():
                    message = TelegramTestMessage(record)
            return message

    def send_messages(self) -> None:
        """
        Sends all messages stored in the factory.

        This method iterates through all stored messages and sends each one.
        After sending, it clears the stored messages dictionary.
        """
        for message in self._messages.values():
            message.send()
        self._messages = {}

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
        records = self._router.prepare_next(user_id)
        for item in records:
            match item:
                case OpenQuestion():
                    record = OpenRecord(question_id=item.question_id, person_id=item.person_id)
                    self.create_open(record)
                case TestQuestion():
                    record = TestRecord(question_id=item.question_id, person_id=item.person_id)
                    self.create_test(record)
                case TestRecord():
                    self.create_test(item)
                case OpenRecord():
                    self.create_open(item)

        self.send_messages()

    def create_open(self, record: OpenRecord) -> None:
        """
        Creates a TelegramOpenMessage from an OpenRecord.

        :param record: (:class:`OpenRecord`) The OpenRecord object to create the message from.
        """
        self._messages[record.message_id] = TelegramOpenMessage(record)

    def create_test(self, record: TestRecord) -> None:
        """
        Creates a TelegramTestMessage from a TestRecord.

        :param record: (:class:`TestRecord`) The TestRecord object to create the message from.
        """
        self._messages[record.message_id] = TelegramTestMessage(record)
