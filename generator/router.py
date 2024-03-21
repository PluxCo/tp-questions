from core.answers import Record
from core.questions import Question
from generator.generators import Generator
from telegram_connector.TelegramMessageFactory import TelegramMessageFactory
from telegram_connector.Webhook import Webhook
from users import Person


class PersonRouter():
    def __init__(self, generator: Generator):
        self.generator = generator
        self._factory = TelegramMessageFactory()
        Webhook._factory = self._factory

    def prepare_next(self, person_id):
        items = self.generator.next_bunch(Person.get_person(person_id))
        for item in items:
            if isinstance(item, Question):
                item.init_record(person_id).dispatch(self._factory)
            elif isinstance(item, Record):
                item.dispatch(self._factory)

    def route_multiple(self):
        for person in Person.get_all_people():
            self.prepare_next(person.id)
        self._factory.send_messages()
