import datetime
import unittest

from sqlalchemy import select, func

# noinspection PyUnresolvedReferences
from core import answers, questions
from core.answers import Record, TestRecord, OpenRecord, AnswerState
from core.questions import TestQuestion, Question, OpenQuestion
from db_connector import SqlAlchemyBase, DBWorker


class DatabaseConnectionTestCase(unittest.TestCase):
    def test_without_init(self):
        DBWorker.reset_connection()
        self.assertRaises(AttributeError, DBWorker().__enter__)

    def test_full_init(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.assertNotEqual(set(), set(SqlAlchemyBase.metadata.tables.keys()))

    def test_reinit(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)

        prev_engine = DBWorker._engine
        prev_maker = DBWorker._maker

        DBWorker.init_db_file("sqlite:///:memory:")

        self.assertIs(prev_engine, DBWorker._engine)
        self.assertIs(prev_maker, DBWorker._maker)

    def test_context_open(self):
        from sqlalchemy import select
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        with DBWorker() as db:
            print(db.scalars(select(Question)).all())


class QuestionCreationTestCase(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_create_test(self):
        question = TestQuestion(text='Sample Question',
                                subject='Sample Subject',
                                options=["option 1", "option 2", "option 2"],
                                answer='1',
                                level=2,
                                article_url='https://example.com')

        self.session.add(question)
        self.session.commit()


class SingleTestQuestionTestCase(unittest.TestCase):
    question = None
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

        cls.question = TestQuestion(text='Sample Question',
                                    subject='Sample Subject',
                                    options=["option 1", "option 2", "option 2"],
                                    answer='1',
                                    level=2,
                                    article_url='https://example.com')
        cls.session.add(cls.question)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up resources after each test
        cls.session.close()

    def test_instances(self):
        self.assertIsInstance(self.question, Question)
        self.assertIsInstance(self.question, TestQuestion)
        self.assertNotIsInstance(self.question, OpenQuestion)

        question = self.session.get(Question, self.question.id)

        self.assertIsInstance(question, Question)
        self.assertIsInstance(question, TestQuestion)
        self.assertNotIsInstance(question, OpenQuestion)

        question = self.session.get(TestQuestion, self.question.id)

        self.assertIsInstance(question, Question)
        self.assertIsInstance(question, TestQuestion)
        self.assertNotIsInstance(question, OpenQuestion)

    def test_answer_init(self):
        record = self.question.init_record()

        self.assertIsInstance(record, Record)
        self.assertIsInstance(record, TestRecord)
        self.assertNotIsInstance(record, OpenRecord)


class SingleOpenQuestionTestCase(unittest.TestCase):
    question = None
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

        cls.question = OpenQuestion(text='Sample Question',
                                    subject='Sample Subject',
                                    answer='Test Message',
                                    level=2,
                                    article_url='https://example.com')
        cls.session.add(cls.question)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up resources after each test
        cls.session.close()

    def test_test_question_attributes(self):
        # Test if attributes are set up correctly

        question = self.session.get(Question, self.question.id)

        self.assertEqual(question.text, 'Sample Question')
        self.assertEqual(question.subject, 'Sample Subject')
        self.assertEqual(question.answer, 'Test Message')
        self.assertEqual(question.level, 2)
        self.assertEqual(question.article_url, 'https://example.com')

    def test_instances(self):
        self.assertIsInstance(self.question, Question)
        self.assertIsInstance(self.question, OpenQuestion)
        self.assertNotIsInstance(self.question, TestQuestion)

        question = self.session.get(Question, self.question.id)

        self.assertIsInstance(question, Question)
        self.assertIsInstance(question, OpenQuestion)
        self.assertNotIsInstance(question, TestQuestion)

        question = self.session.get(OpenQuestion, self.question.id)

        self.assertIsInstance(question, Question)
        self.assertIsInstance(question, OpenQuestion)
        self.assertNotIsInstance(question, TestQuestion)

    def test_answer_init(self):
        record = self.question.init_record()

        self.assertIsInstance(record, Record)
        self.assertIsInstance(record, OpenRecord)
        self.assertNotIsInstance(record, TestRecord)


class TestQuestionCRUDTestCase(unittest.TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        self.question = TestQuestion(text='Sample Question',
                                     subject='Sample Subject',
                                     options=["option 1", "option 2", "option 3"],
                                     answer='1',
                                     level=2,
                                     article_url='https://example.com')

        self.session.add(self.question)
        self.session.commit()
        record = self.question.init_record()
        record.ask_time = datetime.datetime.now()
        record.state = AnswerState.NOT_ANSWERED
        record.person_id = "1"
        self.session.add(record)
        record = self.question.init_record()
        record.ask_time = datetime.datetime.now()
        record.state = AnswerState.NOT_ANSWERED
        record.person_id = "1"
        self.session.add(record)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_attributes(self):
        self.assertEqual(self.question.text, 'Sample Question')
        self.assertEqual(self.question.subject, 'Sample Subject')
        self.assertEqual(self.question.options, ["option 1", "option 2", "option 3"])
        self.assertEqual(self.question.answer, '1')
        self.assertEqual(self.question.level, 2)
        self.assertEqual(self.question.article_url, 'https://example.com')

    def test_edit(self):
        self.question.text = "q2"
        self.question.subject = ""
        self.question.options = ["test"]
        self.question.answer = "0"
        self.question.level = 3
        self.question.article_url = "https://example.com/test"

        self.assertEqual(self.question.text, 'q2')
        self.assertEqual(self.question.subject, '')
        self.assertEqual(self.question.options, ["test"])
        self.assertEqual(self.question.answer, '0')
        self.assertEqual(self.question.level, 3)
        self.assertEqual(self.question.article_url, 'https://example.com/test')

    def test_delete(self):
        q_id = self.question.id
        count = self.session.scalar(select(func.count(Record.id)).where(Record.question_id == q_id))

        self.assertEqual(2, count)

        self.session.delete(self.question)

        count = self.session.scalar(select(func.count(Record.id)).where(Record.question_id == q_id))
        self.assertEqual(0, count)


if __name__ == '__main__':
    unittest.main()
