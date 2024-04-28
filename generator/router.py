import datetime
import logging

from sqlalchemy.orm import Session

from core.answers import Record
from core.questions import Question
from db_connector import DBWorker
from generator.generators import Generator
from telegram_connector.telegram_message_factory import TelegramMessageFactory
from telegram_connector.webhook import Webhook
from users import Person

logger = logging.getLogger(__name__)


class PersonRouter:
    """
    Router for the generator class that handles routing of messages.
    """

    def __init__(self, generator: Generator):
        """
        Initialize the PersonRouter.


        :param generator: (:class:`Generator`:) The generator object to use for generating messages.
        """
        self.generator = generator
        self._factory = TelegramMessageFactory(self)
        Webhook._factory = self._factory

    def prepare_next(self, person_id: str, db_worker: Session = None):
        """
        Prepares the next question/record to send to the person.

        :param person_id: (:class:`str`): The ID of the person for whom the question is prepared.
        :param db_worker: (:class:`Session`, optional): The database worker used to communicate with the database.
        """
        try:
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
                logger.debug(f"Question/record for person {person_id} has been prepared")
        except Exception as e:
            logger.exception(f"An error occurred while preparing next question/record for person {person_id}: {str(e)}")

    def route_multiple(self):
        """
        Prepares and sends questions/records to multiple people.
        """
        try:
            with DBWorker() as db:
                for person in Person.get_all_people():
                    self.prepare_next(person.id, db)
            self._factory.send_messages()
            logger.debug("Messages sent")
        except Exception as e:
            logger.exception(e)
            print(f"An error occurred while routing questions/records to multiple people: {str(e)}")
