from generator.generators import Generator
from users import Person


class PersonRouter():
    def __init__(self, generator: Generator):
        self.generator = generator

    def prepare_next(self, person_id):
        return self.generator.next_bunch(Person.get_person(person_id))

    def prepare_multiple(self):
        pass
