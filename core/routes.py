"""Routes module that contains an abstract classes
for sending information outside"""
from abc import ABC, abstractmethod

from answers import OpenRecord, TestRecord


class PointsCalculator(ABC):
    """
    Abstract class that defines the interface for scoring records
    """
    @abstractmethod
    def score_open(self, record: OpenRecord) -> float:
        """
        Method that score open records

        :param record: scorable open record
        :type record: OpenRecord

        :return: answer points
        :rtype: float
        """

    @abstractmethod
    def score_test(self, record: TestRecord) -> float:
        """
        Method that score test records

        :param record: scorable test record
        :type record: TestRecord

        :return: answer points
        :rtype: float
        """


class MessageFactory(ABC):
    """
    Abstract class for presentation questions to user
    """
    @abstractmethod
    def create_open(self, record: OpenRecord) -> None:
        """
        Handle dispatching open records

        :param record: open record for presenting
        :type record: OpenRecord

        :return: None
        """

    @abstractmethod
    def create_test(self, record: TestRecord) -> None:
        """
        Handle dispatching test records

        :param record: test record for presenting
        :type record: TestRecord

        :return: None
        """
