"""
Telegram message
This module provides a wrapper around a Telegram message
"""
import json
import os
from abc import ABC, abstractmethod

import requests

from calculators.SimpleCalculator import SimpleCalculator
from core.answers import Record, OpenRecord, TestRecord
from db_connector import DBWorker


class TelegramMessage(ABC):
    """
    Abstract class that represents a Telegram message.
    """

    def __init__(self, record: Record):
        self._record = record
        self._service_id = os.getenv("SERVICE_ID")
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

    def handle_answer(self, answer: dict):
        if answer["type"] == "BUTTON":
            raise ValueError('Button not supported')
        text = answer["text"]

        with DBWorker() as db:
            self._record = db.merge(self._record)
            self._record.set_answer(text)
            score = self._record.score(SimpleCalculator())
            request = {"service_id": self._service_id,
                       "messages": [{
                           "user_id": self._record.person_id,
                           "type": "SIMPLE",
                           "text": f"На мой субъективный взгляд, ответ на {score}, "
                                   "однако потом оценку могут изменить."
                       }]}

            db.commit()

        requests.post(self._destination, json=request)

    def send(self):
        with DBWorker() as db:
            self._record = db.merge(self._record)
            message = {
                "user_id": self._record.person_id,
                "text": self._record.question.text,
                "type": "SIMPLE",
            }

            resp = requests.post(self._destination,
                                 json={"service_id": self._service_id,
                                       "messages": [message]})
            self.message_id = resp.json()["sent_messages"][0]["message_id"]
            self._record.transfer(self.message_id)
            db.commit()


class TelegramTestMessage(TelegramMessage):
    def __init__(self, test_record: TestRecord):
        super().__init__(test_record)

    def handle_answer(self, answer: dict):
        if answer["type"] != "BUTTON":
            raise ValueError('Reply or Simple Message not supported')
        text = str(answer["button_id"])

        with DBWorker() as db:
            self._record = db.merge(self._record)
            self._record.set_answer(text)
            score = self._record.score(SimpleCalculator())

            if score == 1:
                request = {
                    "service_id": self._service_id,
                    "messages": [{
                        "user_id": self._record.person_id,
                        "type": "SIMPLE",
                        "text": "Ответ верный!"
                    }]}
            else:
                request = {
                    "service_id": self._service_id,
                    "messages": [{
                        "user_id": self._record.person_id,
                        "type": "SIMPLE",
                        "text": "Ответ неверный ;("
                    }]}
            db.commit()

        requests.post(self._destination, json=request)

    def send(self):
        with DBWorker() as db:
            self._record = db.merge(self._record)
            message = {
                "user_id": self._record.person_id,
                "type": "WITH_BUTTONS",
                "text": self._record.question.text,
                "buttons": ["Не знаю"] + json.loads(self._record.question.options)
            }
            resp = requests.post(self._destination,
                                 json={"service_id": self._service_id,
                                       "messages": [message]})
            self.message_id = resp.json()["sent_messages"][0]["message_id"]
            self._record.transfer(self.message_id)
            db.commit()
