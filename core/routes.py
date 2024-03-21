"""Routes module that contains abstract classes
for sending information outside"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.answers import OpenRecord, TestRecord


class PointsCalculator(ABC):
    """
    Abstract class that defines the interface to score records
    """

    @abstractmethod
    def score_open(self, record: OpenRecord) -> float:
        """
        Method that scores open records

        :param record: scorable open record
        :type record: OpenRecord

        :return: answer points
        :rtype: float
        """

    @abstractmethod
    def score_test(self, record: TestRecord) -> float:
        """
        Method that scores test records

        :param record: scorable test record
        :type record: TestRecord

        :return: answer points
        :rtype: float
        """


class MessageFactory(ABC):
    """
    Abstract class that presents questions to users
    """

    @abstractmethod
    def create_open(self, record: OpenRecord) -> None:
        """
        Handles dispatching of open records

        :param record: open record to present
        :type record: OpenRecord

        :return: None
        """

    @abstractmethod
    def create_test(self, record: TestRecord) -> None:
        """
        Handles dispatching of test records

        :param record: test record to present
        :type record: TestRecord

        :return: None
        """
