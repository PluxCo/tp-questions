"""File that describes records of answers and their specific behavior."""
from __future__ import annotations

import datetime
import enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from db_connector import SqlAlchemyBase

if TYPE_CHECKING:
    from core.questions import Question
    from core.routes import PointsCalculator, MessageFactory


class AnswerState(enum.Enum):
    """
    Enumeration of possible record states for :class:`Record`

    :cvar NOT_ANSWERED: The answer has not been provided.
    :cvar TRANSFERRED: The answer has been transferred to an external system.
    :cvar PENDING: The answer is pending for a review.
    :cvar ANSWERED: The answer has been provided.
    """

    NOT_ANSWERED = 0
    TRANSFERRED = 1
    PENDING = 3
    ANSWERED = 2


class Record(SqlAlchemyBase, SerializerMixin):
    r"""
    Abstract class that represents an answer record of a particular question.

    :cvar id: (:class:`int`) The primary key of the answer.
    :cvar type: (:class:`str`) The type of the answer
    :cvar question_id: (:class:`int`) Foreign key referencing the questions table.
    :cvar question: (:class:`Question`) Relationship to the corresponding question.
    :cvar person_id: (:class:`str`) The ID of the person providing the answer.
    :cvar person_answer: (:class:`Optional`\[:class:`str`]) The answer provided by the person.
    :cvar answer_time: (:class:`Optional`\[:class:`datetime.datetime`]) The time when the answer was provided.
    :cvar ask_time: (:class:`datetime.datetime`) The time when the question was asked.
    :cvar state: (:class:`AnswerState`) The state of the answer.
    :cvar points: (:class:`int`) Amount of points scored for this answer (from 0 to 1)
    """

    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["Question"] = relationship(lazy="joined", back_populates="_records")
    person_id: Mapped[str]
    message_id: Mapped[str]
    person_answer: Mapped[Optional[str]]
    answer_time: Mapped[Optional[datetime.datetime]]
    ask_time: Mapped[datetime.datetime]
    state: Mapped[AnswerState]
    points: Mapped[float] = mapped_column(default=0)

    __mapper_args__ = {"polymorphic_identity": "record", "polymorphic_on": "type"}

    def __init__(self, *args, **kwargs):
        r""":key id: (:class:`int`) The primary key of the answer.
        :key type: (:class:`str`) The type of the answer
        :key question_id: (:class:`int`) Foreign key referencing the questions table.
        :key question: (:class:`Question`) Relationship to the corresponding question.
        :key person_id: (:class:`str`) The ID of the person providing the answer.
        :key person_answer: (:class:`Optional`\[:class:`str`]) The answer provided by the person.
        :key answer_time: (:class:`Optional`\[:class:`datetime.datetime`]) The time when the answer was provided.
        :key ask_time: (:class:`datetime.datetime`) The time when the question was asked.
        :key state: (:class:`AnswerState`) The state of the answer.
        :key points: (:class:`int`) Amount of points scored for this answer (from 0 to 1)
        """
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<AnswerRecord(q_id={self.question_id}, state={self.state}, person_id={self.person_id})>"

    def score(self, calculator: PointsCalculator) -> float:
        """
        An abstract method that should score record and change :class:`AnswerState`

        :param calculator: calculator that should be used to calculate points
        :type calculator: PointsCalculator

        :return: points that should be applied
        :rtype: float
        """

    def dispatch(self, factory: MessageFactory):
        """
        An abstract method that dispatches questions to associated factory

        :param factory: factory that handles dispatched records
        :type factory: MessageFactory

        :return: None
        """

    def transfer(self, message_id):
        """Method that changes :class:`RecordState` after transferring"""

        # noinspection PyTypeChecker
        self.state = AnswerState.TRANSFERRED
        self.message_id = message_id

    def set_answer(self, answer: str) -> None:
        """
        Method that sets the user answer

        :param answer: user answer
        :type answer: str

        :return: None
        """

        # noinspection PyTypeChecker
        self.person_answer = answer


class TestRecord(Record):
    """
    TestRecord is an instance of :class:`Record`
    """

    __mapper_args__ = {"polymorphic_identity": "TEST"}

    # noinspection PyTypeChecker
    def score(self, calculator: PointsCalculator) -> float:
        self.points = calculator.score_test(self)

        self.state = AnswerState.ANSWERED
        return self.points

    def dispatch(self, factory: MessageFactory):
        factory.create_test(self)


class OpenRecord(Record):
    """
    OpenRecord is an instance of :class:`Record`
    """

    __mapper_args__ = {"polymorphic_identity": "OPEN"}

    # noinspection PyTypeChecker
    def score(self, calculator: PointsCalculator) -> float:
        self.points = calculator.score_open(self)

        self.state = AnswerState.PENDING
        return self.points

    def dispatch(self, factory: MessageFactory):
        factory.create_open(self)
