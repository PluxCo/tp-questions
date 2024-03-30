import datetime
import unittest
from unittest import TestCase
from unittest.mock import Mock

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
        DBWorker.init_db_file("sqlite:///:memory:", force=True)


class QuestionCreationTestCase(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_test_question_creation(self):
        question = TestQuestion(text='Sample Question',
                                subject='Sample Subject',
                                options=["option 1", "option 2", "option 2"],
                                answer='1',
                                level=2,
                                article_url='https://example.com')

        self.session.add(question)
        self.session.commit()

    def test_open_question_creation(self):
        question = OpenQuestion(text='Sample Question',
                                subject='Sample Subject',
                                answer='That is an answer',
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
        record = self.question.init_record('user 1')

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

    def test_question_attributes(self):
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
        record = self.question.init_record('user 1')

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

        record = self.question.init_record('user 1')
        record.ask_time = datetime.datetime.now()
        record.state = AnswerState.NOT_ANSWERED
        record.person_id = "1"
        self.session.add(record)

        record = self.question.init_record('user 1')
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


class OpenQuestionCRUDTestCase(TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        self.question = OpenQuestion(text='Sample Question',
                                     subject='Sample Subject',
                                     answer='That is an answer',
                                     level=2,
                                     article_url='https://example.com')

        self.session.add(self.question)
        self.session.commit()

        record = self.question.init_record('user 1')
        record.ask_time = datetime.datetime.now()
        record.state = AnswerState.NOT_ANSWERED
        record.person_id = "1"
        self.session.add(record)

        record = self.question.init_record('user 1')
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
        self.assertEqual(self.question.answer, 'That is an answer')
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


class RecordCreationTestCase(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_test_record_creation(self):
        question = TestQuestion(
            id=1,
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )

        record = TestRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing purposes
        )

        self.session.add(question)
        self.session.add(record)
        self.session.commit()

    def test_open_record_creation(self):
        question = OpenQuestion(
            id=2,
            text='Sample Question',
            answer='1',
            level=2,
            type='OPEN'
        )

        record = OpenRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing purposes
        )

        self.session.add(question)
        self.session.add(record)
        self.session.commit()


class SingleTestRecordTestCase(unittest.TestCase):
    record = None
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

        question = TestQuestion(
            id=1,
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )

        cls.record = TestRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        cls.session.add(question)
        cls.session.add(cls.record)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up resources after each test
        cls.session.close()

    def test_instances(self):
        self.assertIsInstance(self.record, Record)
        self.assertIsInstance(self.record, TestRecord)
        self.assertNotIsInstance(self.record, OpenRecord)

        retrieved_record = self.session.get(Record, self.record.id)

        self.assertIsInstance(retrieved_record, Record)
        self.assertIsInstance(retrieved_record, TestRecord)
        self.assertNotIsInstance(retrieved_record, OpenRecord)

        retrieved_record = self.session.get(TestRecord, self.record.id)

        self.assertIsInstance(retrieved_record, Record)
        self.assertIsInstance(retrieved_record, TestRecord)
        self.assertNotIsInstance(retrieved_record, OpenRecord)

    def test_attributes(self):
        retrieved_record = self.session.get(TestRecord, self.record.id)

        self.assertEqual(retrieved_record.question_id, self.record.question_id)
        self.assertEqual(retrieved_record.state, self.record.state)
        self.assertEqual(retrieved_record.person_answer, self.record.person_answer)
        self.assertEqual(retrieved_record.points, self.record.points)
        self.assertEqual(retrieved_record.ask_time, self.record.ask_time)
        self.assertEqual(retrieved_record.answer_time, self.record.answer_time)
        self.assertEqual(retrieved_record.person_id, self.record.person_id)

    def test_scoring(self):
        mock_calculator = Mock()
        mock_calculator.score_test = Mock(return_value=1)

        self.record.score(calculator=mock_calculator)

        self.assertEqual(self.record.points, 1)
        self.assertNotEqual(self.record.points, 0.5)
        self.assertEqual(self.record.state, AnswerState.ANSWERED)
        mock_calculator.score_test.assert_called_once()

        self.session.rollback()

    def test_transferring(self):
        retrieved_record = self.session.get(TestRecord, self.record.id)
        retrieved_record.transfer('message 1')

        self.assertEqual(self.record.state, AnswerState.TRANSFERRED)

        self.session.rollback()

    def test_answering(self):
        retrieved_record = self.session.get(TestRecord, self.record.id)

        retrieved_record.set_answer(answer='2')

        self.assertEqual(self.record.person_answer, '2')
        self.session.rollback()

    def test_dispatching(self):
        retrieved_record = self.session.get(TestRecord, self.record.id)
        mock_message_factory = Mock()
        mock_message_factory.create_test = Mock()

        retrieved_record.dispatch(factory=mock_message_factory)
        mock_message_factory.create_test.assert_called_once()


class SingleOpenRecordTestCase(unittest.TestCase):
    record = None
    session = None

    @classmethod
    def setUpClass(cls):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        cls.session = DBWorker().session

        question = OpenQuestion(
            id=1,
            text='Sample Question',
            answer='That\'s the answer...',
            level=2,
            type='OPEN'
        )

        cls.record = OpenRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='That\'s an open question for sure',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        cls.session.add(question)
        cls.session.add(cls.record)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up resources after each test
        cls.session.close()

    def test_instances(self):
        self.assertIsInstance(self.record, Record)
        self.assertIsInstance(self.record, OpenRecord)
        self.assertNotIsInstance(self.record, TestRecord)

        retrieved_record = self.session.get(Record, self.record.id)

        self.assertIsInstance(retrieved_record, Record)
        self.assertIsInstance(retrieved_record, OpenRecord)
        self.assertNotIsInstance(retrieved_record, TestRecord)

        retrieved_record = self.session.get(OpenRecord, self.record.id)

        self.assertIsInstance(retrieved_record, Record)
        self.assertIsInstance(retrieved_record, OpenRecord)
        self.assertNotIsInstance(retrieved_record, TestRecord)

    def test_attributes(self):
        retrieved_record = self.session.get(OpenRecord, self.record.id)

        self.assertEqual(retrieved_record.question_id, self.record.question_id)
        self.assertEqual(retrieved_record.state, self.record.state)
        self.assertEqual(retrieved_record.person_answer, self.record.person_answer)
        self.assertEqual(retrieved_record.points, self.record.points)
        self.assertEqual(retrieved_record.ask_time, self.record.ask_time)
        self.assertEqual(retrieved_record.answer_time, self.record.answer_time)
        self.assertEqual(retrieved_record.person_id, self.record.person_id)

    def test_scoring(self):
        mock_calculator = Mock()
        mock_calculator.score_open = Mock(return_value=1)

        self.record.score(calculator=mock_calculator)

        self.assertEqual(self.record.points, 1)
        self.assertNotEqual(self.record.points, 0.5)
        self.assertEqual(self.record.state, AnswerState.PENDING)
        mock_calculator.score_open.assert_called_once()

        self.session.rollback()

    def test_transferring(self):
        retrieved_record = self.session.get(OpenRecord, self.record.id)
        retrieved_record.transfer('message id')

        self.assertEqual(self.record.state, AnswerState.TRANSFERRED)

        self.session.rollback()

    def test_answering(self):
        retrieved_record = self.session.get(OpenRecord, self.record.id)

        retrieved_record.set_answer(answer='Wow that\'s the answer!?')

        self.assertEqual(self.record.person_answer, 'Wow that\'s the answer!?')
        self.session.rollback()

    def test_dispatching(self):
        retrieved_record = self.session.get(OpenRecord, self.record.id)
        mock_message_factory = Mock()
        mock_message_factory.create_open = Mock()

        retrieved_record.dispatch(factory=mock_message_factory)
        mock_message_factory.create_open.assert_called_once()


class OpenRecordCRUDTestCase(TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        question = OpenQuestion(
            id=1,
            text='Sample Question',
            answer='That\'s the answer...',
            level=2,
            type='OPEN'
        )

        self.record = OpenRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='That\'s an open question for sure',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        self.session.add(question)
        self.session.add(self.record)
        self.session.commit()

    def tearDown(self):
        # Clean up resources after each test
        self.session.close()

    def test_edit(self):
        self.record.person_id = 'user_2'
        self.record.person_answer = 'That\'s a test question for sure (NOPE)'
        self.record.ask_time = datetime.datetime(1, 2, 3, 4, 5, 6)
        self.record.state = AnswerState.ANSWERED
        self.record.points = 1

        self.assertEqual(self.record.person_id, 'user_2')
        self.assertEqual(self.record.person_answer, 'That\'s a test question for sure (NOPE)')
        self.assertEqual(self.record.ask_time, datetime.datetime(1, 2, 3, 4, 5, 6))
        self.assertEqual(self.record.state, AnswerState.ANSWERED)
        self.assertEqual(self.record.points, 1)

    def test_delete(self):
        record_id = self.record.id
        count = self.session.scalar(select(func.count(Record.id)).where(Record.id == record_id))

        self.assertEqual(1, count)

        self.session.delete(self.record)

        count = self.session.scalar(select(func.count(Record.id)).where(Record.id == record_id))
        self.assertEqual(0, count)


class TestRecordCRUDTestCase(TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        question = TestQuestion(
            id=1,
            text='Sample Question',
            options=["BAbE", "Gabe", "LAbe"],
            answer='1',
            level=2,
            type='TEST'
        )

        self.record = TestRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        self.session.add(question)
        self.session.add(self.record)
        self.session.commit()

    def tearDown(self):
        # Clean up resources after each test
        self.session.close()

    def test_edit(self):
        self.record.person_id = 'user_2'
        self.record.person_answer = '2'
        self.record.ask_time = datetime.datetime(1, 2, 3, 4, 5, 6)
        self.record.state = AnswerState.ANSWERED
        self.record.points = 1

        self.assertEqual(self.record.person_id, 'user_2')
        self.assertEqual(self.record.person_answer, '2')
        self.assertEqual(self.record.ask_time, datetime.datetime(1, 2, 3, 4, 5, 6))
        self.assertEqual(self.record.state, AnswerState.ANSWERED)
        self.assertEqual(self.record.points, 1)

    def test_delete(self):
        record_id = self.record.id
        count = self.session.scalar(select(func.count(Record.id)).where(Record.id == record_id))

        self.assertEqual(1, count)

        self.session.delete(self.record)

        count = self.session.scalar(select(func.count(Record.id)).where(Record.id == record_id))
        self.assertEqual(0, count)


if __name__ == '__main__':
    unittest.main()
