import datetime
import os
import unittest
from unittest.mock import patch

from requests import Response
from sqlalchemy import select

from core.answers import OpenRecord, AnswerState, TestRecord
from core.questions import OpenQuestion, TestQuestion
from db_connector import DBWorker
from generator.generators import SimpleGenerator
from generator.router import PersonRouter
from telegram_connector.telegram_message import TelegramOpenMessage, TelegramTestMessage
from telegram_connector.telegram_message_factory import TelegramMessageFactory


class HelpfulGenerators:
    @staticmethod
    def generate_open_record(session):
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
        session.add(question)
        session.add(record)
        session.commit()
        return {"session": session, "question": question, "record": record}

    @staticmethod
    def generate_test_record(session):
        question = TestQuestion(text='Sample Question',
                                id=3,
                                subject='Sample Subject',
                                options=['1', '2', '3', '4'],
                                answer='1',
                                level=1,
                                article_url='https://example.com')

        record = TestRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )
        session.add(question)
        session.add(record)
        session.commit()
        return {"session": session, "question": question, "record": record}


class TestTelegramSendingMessage(unittest.TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        open_question = OpenQuestion(
            id=2,
            text='Sample Question',
            answer='1',
            level=2,
            type='OPEN'
        )

        self.open_record = OpenRecord(
            question_id=open_question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing purposes
        )
        self.session.add(open_question)
        self.session.add(self.open_record)

        test_question = TestQuestion(text='Sample Question',
                                     id=3,
                                     subject='Sample Subject',
                                     options='["1", "2", "3", "4"]',
                                     answer='1',
                                     level=1,
                                     article_url='https://example.com')

        self.test_record = TestRecord(
            question_id=test_question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )
        self.session.add(test_question)
        self.session.add(self.test_record)
        self.session.commit()

    def tearDown(self):
        # Clean up resources after each test
        self.session.close()

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_open_message(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()
        self.assertEqual("123", message.message_id)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_test_message(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()
        self.assertEqual("123", message.message_id)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_sending_test_message(self, mock_post):
        test_message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        test_message.send()

        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [{'user_id': 'user_1',
                                                                                       'type': 'WITH_BUTTONS',
                                                                                       'text': 'Sample Question',
                                                                                       'buttons': ['Не знаю', '1', '2',
                                                                                                   '3', '4']}]})

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_sending_open_message(self, mock_post):
        open_message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        open_message.send()

        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [{'user_id': 'user_1',
                                                                                       'text': 'Sample Question',
                                                                                       'type': 'SIMPLE'}]})

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_updating_db_test_question(self, mock_post):
        test_message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        test_message.send()
        with DBWorker() as db:
            updated_test_record = db.scalar(
                select(TestRecord).where(TestRecord.message_id == "123", TestRecord.person_id == "user_1"))

        self.assertNotEqual(None, updated_test_record)
        self.assertEqual(updated_test_record.state, AnswerState.TRANSFERRED)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_updating_db_open_question(self, mock_post):
        open_message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        open_message.send()
        with DBWorker() as db:
            updated_open_record = db.scalar(
                select(OpenRecord).where(OpenRecord.message_id == "123", OpenRecord.person_id == "user_1"))

        self.assertNotEqual(None, updated_open_record)
        self.assertEqual(updated_open_record.state, AnswerState.TRANSFERRED)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_open_message_with_weird_status_code(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 418  # I’m a teapot
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        self.assertRaises(Exception, message.send)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_test_message_with_weird_status_code(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 418  # I’m a teapot
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        self.assertRaises(Exception, message.send)
        # А проверки на status code и нет. А вдруг придут испорченные данные(corrupted/корумпированные)?

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_open_message_with_messed_up_response_message_id(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 418  # I’m a teapot
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "aaa"}]}'

        mock_post.return_value = resp
        self.assertRaises(Exception, message.send)  # Никаких проверок, что message id int

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_test_message_with_messed_up_response_message_id(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 418  # I’m a teapot
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "aaa"}]}'

        mock_post.return_value = resp

        self.assertRaises(Exception, message.send)  # Никаких проверок, что message id int

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_open_message_with_messed_up_response(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": []}'

        mock_post.return_value = resp
        self.assertRaises(Exception, message.send)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_catching_response_test_message_with_messed_up_response(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": []}'

        mock_post.return_value = resp

        self.assertRaises(Exception, message.send)


class TestTelegramHandlingAnswers(unittest.TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        open_question = OpenQuestion(
            id=2,
            text='Sample Question',
            answer='1',
            level=2,
            type='OPEN'
        )

        self.open_record = OpenRecord(
            question_id=open_question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing purposes
        )
        self.session.add(open_question)
        self.session.add(self.open_record)

        test_question = TestQuestion(text='Sample Question',
                                     id=3,
                                     subject='Sample Subject',
                                     options='["1", "2", "3", "4"]',
                                     answer='1',
                                     level=1,
                                     article_url='https://example.com')

        self.test_record = TestRecord(
            question_id=test_question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )
        self.session.add(test_question)
        self.session.add(self.test_record)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_handling_open_message_answer(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()

        message.handle_answer('0')
        self.assertNotEqual(None, mock_post.mock_calls[1])
        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [
                                                                             {'user_id': 'user_1', 'type': 'SIMPLE',
                                                                              'text': 'На мой субъективный взгляд, '
                                                                                      'ответ на 0.5, однако потом '
                                                                                      'оценку могут изменить.'}]})

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_handling_incorrect_test_message_answer(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()

        message.handle_answer('0')
        self.assertNotEqual(None, mock_post.mock_calls[1])
        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [
                                                                             {'user_id': 'user_1', 'type': 'SIMPLE',
                                                                              'text': 'Ответ неверный ;('}]})

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_handling_correct_test_message_answer(self, mock_post):
        message = TelegramTestMessage(self.test_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()

        message.handle_answer('1')
        self.assertNotEqual(None, mock_post.mock_calls[1])
        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [
                                                                             {'user_id': 'user_1', 'type': 'SIMPLE',
                                                                              'text': 'Ответ верный!'}]})

    # Тест на оценку открытого ответа полностью совпадающего с эталонным ответом. Пока не работает
    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_handling_correct_open_message_answer(self, mock_post):
        message = TelegramOpenMessage(self.open_record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()

        message.handle_answer('1')
        self.assertNotEqual(None, mock_post.mock_calls[1])
        mock_post.assert_called_with('http://example.com/message', json={'webhook': 'http://example.com/webhook/',
                                                                         'messages': [
                                                                             {'user_id': 'user_1', 'type': 'SIMPLE',
                                                                              'text': 'На мой субъективный взгляд, '
                                                                                      'ответ на 1.0, однако потом '
                                                                                      'оценку могут изменить.'}]})


# I don't ****ing know how to make webhook api working as separated module. Its keep making message factory error. Sry
# class WebhookTests(unittest.TestCase):
#     def setUp(self):
#         self.router = PersonRouter(SimpleGenerator())
#         self.app = app.test_client()
#         DBWorker.init_db_file("sqlite:///:memory:", force=True)
#         self.session = DBWorker().session
#         logging.basicConfig(level=logging.DEBUG)
#
#     def tearDown(self):
#         self.session.close()
#
#     def test_parse_only_required_arg(self):
#         response = self.app.post('/webhook/', json={'type': 'FEEDBACK'})
#         self.assertEqual(response.status_code, 400)
#         response = self.app.post('/webhook/', json={'type': 'SESSION'})
#         self.assertEqual(response.status_code, 400)
#
#     def test_standart_post_request(self):
#         response = self.app.post('/webhook/', json={'type': 'FEEDBACK', 'feedback':
#             {'type': 'MESSAGE', 'text': "lol"}, 'session': {'user_id': 'user_1', 'state': 'OPEN'}})

class MessageFactoryWorkingTestCase(unittest.TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)

        self.session = DBWorker().session
        temp_dict = HelpfulGenerators.generate_open_record(self.session)
        self.open_record = temp_dict['record']
        temp_dict = HelpfulGenerators.generate_test_record(self.session)
        self.test_record = temp_dict['record']
        self.router = PersonRouter(SimpleGenerator())
        self.factory = TelegramMessageFactory(self.router)

    def tearDown(self):
        self.session.close()

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    def test_creating_messages_is_working(self):
        self.factory.create_open(self.open_record)
        self.assertIs(self.factory._messages[0]._record, self.open_record)
        self.factory.create_test(self.test_record)
        self.assertIs(self.factory._messages[1]._record, self.test_record)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_sending_messages_is_working(self, mock_post):
        self.factory.create_open(self.open_record)
        self.factory.create_test(self.test_record)
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp
        self.factory.send_messages()
        self.assertEqual(mock_post.mock_calls[0][2]['json']['messages'][0],
                         {'user_id': 'user_1', 'text': 'Sample Question', 'type': 'SIMPLE'})
        self.assertEqual(mock_post.mock_calls[1][2]['json']['messages'][0],
                         {'user_id': 'user_1', 'type': 'WITH_BUTTONS', 'text': 'Sample Question',
                          'buttons': ['Не знаю', '1', '2', '3', '4']})

if __name__ == '__main__':
    unittest.main()
