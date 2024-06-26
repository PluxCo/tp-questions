"""
File that describes the questions and specific types of questions
"""
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy_serializer import SerializerMixin

from core.answers import Record, TestRecord, OpenRecord
from db_connector import SqlAlchemyBase
from db_connector.types import TextJson


# noinspection Style,Annotator
class QuestionGroupAssociation(SqlAlchemyBase, SerializerMixin):
    """
    Association table between questions and groups.

    Attributes:
        id (int): The primary key of the association.
        question_id (int): Foreign key referencing the question table.
        group_id (str): The ID of the group associated with the question.
    """
    __tablename__ = "question_to_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    group_id: Mapped[str] = mapped_column()


# noinspection GrazieInspection,Style,Annotator
class Question(SqlAlchemyBase, SerializerMixin):
    r"""
    Represents a question.

    :cvar id: (:class:`int`) The primary key of the question.
    :cvar type: (:class:`int`) The primary key of the question.
    :cvar text: (:class:`str`) The text of the question.
    :cvar subject: (:class:`Optional`\[:class:`str`]) The subject of the question (optional).
    :cvar answer: (:class:`str`) The correct answer to the question.
    :cvar groups: (:class:`List`\[:class:`QuestionGroupAssociation`]) The groups associated with the question.
    :cvar level: (:class:`int`) The difficulty level of the question.
    :cvar article_url: (:class:`Optional`\[:class:`str`]) URL to an article related to the question (optional).
    :cvar type: (:class:`QuestionType`) The type of the answer (TEST, OPEN)

    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]

    text: Mapped[str]
    subject: Mapped[Optional[str]]
    answer: Mapped[str]
    groups: Mapped[List[QuestionGroupAssociation]] = relationship(cascade='all, delete-orphan')
    level: Mapped[int]
    article_url: Mapped[Optional[str]]

    records: Mapped[List[Record]] = relationship(cascade='all, delete-orphan', back_populates='question')

    __mapper_args__ = {"polymorphic_identity": "question", "polymorphic_on": "type"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_record(self, person_id: str) -> Record:
        """
        An abstract method that returns an instance of the associated record
        :return: Record
        """
        return Record(question_id=self.id, person_id=person_id, question=self)


# noinspection GrazieInspection
class TestQuestion(Question):
    """
    Represents a test question.

    :cvar options: (:class:`str`) JSON-encoded options for the question.
    """

    options = mapped_column(TextJson, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "TEST"}

    def init_record(self, person_id: str) -> Record:
        """
        Overrides :meth:`Question.init_record` to provide :class:`TestRecord`

        :return: TestRecord
        """
        return TestRecord(question_id=self.id, person_id=person_id, question=self)


# noinspection GrazieInspection
class OpenQuestion(Question):
    """
    Represents an open question.
    """

    __mapper_args__ = {"polymorphic_identity": "OPEN"}

    def init_record(self, person_id: str) -> Record:
        """
        Overrides :meth:`Question.init_record` to provide :class:`OpenRecord`

        :return: OpenRecord
        """
        return OpenRecord(question_id=self.id, person_id=person_id, question=self)
