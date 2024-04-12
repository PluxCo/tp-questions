import datetime
import os
import unittest
from unittest.mock import patch

from requests import Response

from core.answers import OpenRecord, AnswerState
from core.questions import OpenQuestion
from db_connector import DBWorker
from telegram_connector.telegram_message import TelegramOpenMessage


class TestTelegramOpenMessage(unittest.TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        question = OpenQuestion(
            id=1,
            text='Sample Question',
            answer='1',
            level=2,
        )

        self.record = OpenRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
        )

        self.session.add(question)
        self.session.add(self.record)
        self.session.commit()

    def tearDown(self):
        # Clean up resources after each test
        self.session.close()

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    def test_init_message(self):
        message = TelegramOpenMessage(self.record)
        self.assertIsNone(message.message_id)

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_send_message(self, mock_post):
        message = TelegramOpenMessage(self.record)
        mock_post.return_value.status_code = 200
        resp = Response()
        resp._content = b'{"sent_messages": [{"message_id": "123"}]}'

        mock_post.return_value = resp

        message.send()
        self.assertEqual("123", message.message_id)
        print(mock_post.call_args)





if __name__ == '__main__':
    unittest.main()
