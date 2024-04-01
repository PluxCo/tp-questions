import datetime
import unittest
from unittest import TestCase
from unittest.mock import patch
import os

from core.answers import AnswerState
from core.questions import OpenQuestion, OpenRecord
from db_connector.db_session import DBWorker
from telegram_connector.telegram_message import TelegramOpenMessage, TelegramTestMessage


# Сомнительно, но окей
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


class OpenTelegramMessageTestCase(TestCase):
    def setUp(self):
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self._questions_webhook = os.getenv("QUESTIONS_URL") + "/webhook/"
        self._destination = os.getenv('TELEGRAM_API') + "/message"
        self.session = DBWorker().session
        gen_dict = HelpfulGenerators.generate_open_record(self.session)
        for k, v in gen_dict.items():
            setattr(self, k, v)
        self.telegram_message = TelegramOpenMessage(self.record)

    def tearDown(self):
        # Clean up resources after each test
        self.session.close()

    @patch.dict(os.environ, {"QUESTIONS_URL": "http://example.com", "TELEGRAM_API": "http://example.com"})
    @patch('requests.post')
    def test_sending_message(self, mock_post):
        self.telegram_message.send()
        mock_post.assert_called(os.getenv('TELEGRAM_API') + "/message", )


if __name__ == '__main__':
    unittest.main()
