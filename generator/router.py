"""
The file provides the router class for the generator module.
"""
import datetime

from core.answers import Record
from core.questions import Question
from db_connector import DBWorker
from generator.generators import Generator
from telegram_connector.telegram_message_factory import TelegramMessageFactory
from telegram_connector.webhook import Webhook
from users import Person


# noinspection GrazieInspection,Style,Annotator
class PersonRouter:
    """
    Router for the generator class that handles routing of messages.
    """
    def __init__(self, generator: Generator):
        self.generator = generator
        self._factory = TelegramMessageFactory(self)
        Webhook._factory = self._factory

    def prepare_next(self, person_id: str, db_worker: DBWorker() = None):
        """
        Prepares the question/record to send to the person.
        :param person_id: (:class:`str`) The person for whom the question is prepared
        :param db_worker: (:class:`DBWorker`) The database worker used to communicate with the database.
        """
        items = self.generator.next_bunch(Person.get_person(person_id))
        with DBWorker() if db_worker is None else db_worker as db:
            for item in items:
                if isinstance(item, Question):
                    record = item.init_record(person_id)
                    record.ask_time = datetime.datetime.now()
                    record.dispatch(self._factory)
                    db.add(record)

                elif isinstance(item, Record):
                    item.dispatch(self._factory)

            db.commit()

    def route_multiple(self):
        """
        Prepares the question/record to send to people.
        """
        with DBWorker() as db:
            for person in Person.get_all_people():
                self.prepare_next(person.id, db)
        self._factory.send_messages()
