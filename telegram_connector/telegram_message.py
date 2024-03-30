import json
import os
from abc import ABC, abstractmethod

import requests

from calculators.SimpleCalculator import SimpleCalculator
from core.answers import Record, OpenRecord, TestRecord


class TelegramMessage(ABC):
    def __init__(self, record: Record):
        self._record = record
        self._questions_webhook = os.getenv("QUESTIONS_URL") + "/webhook/"
        self._destination = os.getenv('TELEGRAM_API') + "/message"

        self.message_id = record.message_id

    @abstractmethod
    def send(self):
        """
        Sends message to telegram
        """

    @abstractmethod
    def handle_answer(self, answer):
        """
        Handles answer
        """


class TelegramOpenMessage(TelegramMessage):
    def __init__(self, open_record: OpenRecord):
        super().__init__(open_record)
        self._message = {
            "user_id": open_record.person_id,
            "text": open_record.question.text,
            "type": "SIMPLE",
        }

    def handle_answer(self, answer: str):
        self._record.set_answer(answer)

        score = self._record.score(SimpleCalculator())
        request = {"webhook": self._questions_webhook,
                   "messages": [{
                       "user_id": self._record.person_id,
                       "type": "SIMPLE",
                       "text": f"На мой субъективный взгляд, ответ на {score}, "
                               "однако потом оценку могут изменить."
                   }]}
        requests.post(self._destination, json=request)

    def send(self):
        resp = requests.post(self._destination,
                             json={"webhook": self._questions_webhook,
                                   "messages": [self._message]})
        self.message_id = resp.json()["sent_messages"][0]["message_id"]
        self._record.transfer(self.message_id)


class TelegramTestMessage(TelegramMessage):
    def __init__(self, test_record: TestRecord):
        super().__init__(test_record)
        self._message = {
            "user_id": test_record.person_id,
            "type": "WITH_BUTTONS",
            "text": test_record.question.text,
            "buttons": ["Не знаю"] + json.loads(test_record.question.options)
        }

    def handle_answer(self, answer: str):
        self._record.set_answer(answer)
        score = self._record.score(SimpleCalculator())

        if score == 1:
            request = {
                "webhook": self._questions_webhook,
                "messages": [{
                    "user_id": self._record.person_id,
                    "type": "SIMPLE",
                    "text": "Ответ верный!"
                }]}
        else:
            request = {
                "webhook": self._questions_webhook,
                "messages": [{
                    "user_id": self._record.person_id,
                    "type": "SIMPLE",
                    "text": "Ответ неверный ;("
                }]}

        requests.post(self._destination, json=request)

    def send(self):
        resp = requests.post(self._destination,
                             json={"webhook": self._questions_webhook,
                                   "messages": [self._message]})
        self.message_id = resp.json()["sent_messages"][0]["message_id"]
        self._record.transfer(self.message_id)
