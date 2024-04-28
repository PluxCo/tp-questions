"""
Describes generators used to generate records/questions for people.
"""
import datetime
from abc import ABC, abstractmethod
from typing import Union, Sequence

import numpy as np
from sqlalchemy import select, func

from core.answers import Record, AnswerState
from core.questions import Question, QuestionGroupAssociation
from db_connector import DBWorker
from tools import Settings
from users import Person


# noinspection GrazieInspection,Style,Annotator
class Generator(ABC):
    """
    Abstract base class for question generators.
    """

    @abstractmethod
    def next_bunch(self, person: Person, count: int = 1) -> Sequence[Union[Question, Record]]:
        r"""
        Generates a list of questions or question answers.

        :param person: (:class:`Person`) The person for whom questions are generated.
        :param count: (:class:`int`) The number of questions to generate.
        :return: (:class:`List`\[:class:`Question` | :class:`Record`]) List of generated questions or question answers.
        """

    @staticmethod
    def _get_planned(person: Person, db) -> Sequence[Record]:
        r"""
        Get planned question answers for a person.

        :param person: (:class:`Person`) The person for whom planned question answers are retrieved.
        :return: (:class:`List`\[:class:`Record`]) List of planned question answers.
        """
        return db.scalars(select(Record).
                          where(Record.person_id == person.id,
                                Record.ask_time <= datetime.datetime.now(),
                                Record.state == AnswerState.NOT_ANSWERED).
                          order_by(Record.ask_time)).all()

    @staticmethod
    def _get_person_questions(person: Person, db) -> Sequence[Question]:
        r"""
        Get questions for a person that are not in the planned list.

        :param person: (:class:`Person`) The person for whom questions are retrieved.
        :return: (:class:`List`\[:class:`Question`]) List of questions for the person.
        """
        planned = Generator._get_planned(person, db)

        return db.scalars(select(Question).
                          join(Question.groups).
                          where(QuestionGroupAssociation.group_id.in_(pg for pg, pl in person.groups),
                                Question.id.notin_(qa.question_id for qa in planned)).
                          group_by(Question.id)).all()


# noinspection Style,Annotator
class SimpleGenerator(Generator):
    def next_bunch(self, person: Person, count: int = 1) -> Sequence[Union[Question, Record]]:
        with DBWorker() as db:
            # Get planned questions
            planned = self._get_planned(person, db)
            if len(planned) >= count:
                return planned[:count]

            # Get available questions for the person
            person_questions = self._get_person_questions(person, db)

        # Randomly select questions from available ones

        questions = np.random.choice(person_questions,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)


# noinspection Style,Annotator
class SmartGenerator(Generator):
    def __init__(self, mu=4, sigma=20, correcting_value=0.001):
        self._mu = mu
        self._sigma = sigma
        self._correcting_value = correcting_value

    def next_bunch(self, person, count: int = 1) -> Sequence[Union[Question, Record]]:
        with DBWorker() as db:
            # Get planned questions
            planned = self._get_planned(person, db)
            if len(planned) >= count:
                return planned[:count]

            # Get available questions for the person
            person_questions = self._get_person_questions(person, db)
            probabilities = np.ones(len(person_questions))

            if not person_questions:
                return planned[:count]

            # Calculate probabilities based on user's performance and other factors
            for i, question in enumerate(person_questions):
                question: Question
                points_sum = db.scalar(select(func.sum(Record.points)).
                                       where(Record.person_id == person.id,
                                             Record.question_id == question.id))

                if points_sum:
                    last_answer = db.scalar(select(Record).
                                            join(Record.question).
                                            where(Record.person_id == person.id,
                                                  Record.question_id == question.id).
                                            order_by(Record.ask_time.desc()))

                    first_answer = db.scalar(select(Record).
                                             where(Record.person_id == person.id,
                                                   Record.question_id == question.id))

                    # get rid of this: Settings()["time_period"]
                    periods_count = (datetime.datetime.now() - first_answer.ask_time) / datetime.timedelta(days=1)
                    max_target_level = max(
                        gl for pg, gl in person.groups if pg in [x.group_id for x in question.groups])

                    # P stands for probability. Here we are getting the ratio between number of points and
                    # the time of not answering.
                    p = (datetime.datetime.now() - last_answer.ask_time).total_seconds() / points_sum

                    # deciding whether the question has come at the right time or not with this crazy probability
                    p *= np.abs(np.cos(np.pi * np.log2(periods_count + self._mu))) ** (
                            ((periods_count + self._mu) ** 2) / self._sigma) + self._correcting_value

                    # adding the suitability of level
                    p *= np.exp(-0.5 * (max_target_level - question.level) ** 2)

                    if db.execute(select(func.count(Record.id)).
                                          where(Record.question_id == question.id,
                                                Record.state != AnswerState.ANSWERED)).one()[0] != 0:
                        p *= 0

                    probabilities[i] = p
                else:
                    probabilities[i] = None

            db.expunge_all()

        # with_val = list(filter(lambda x: not np.isnan(x), probabilities))
        # without_val_count = len(person_questions) - len(with_val)

        # if with_val:
        #     increased_avg = (sum(with_val) + without_val_count * max(with_val)) / len(person_questions)
        #     # Да это ж круто!
        # else:
        #     increased_avg = 1

        probabilities[np.isnan(probabilities)] = 10 * np.nanmax(probabilities)

        if not any(probabilities):
            probabilities = np.ones(len(probabilities))

        probabilities /= sum(probabilities)

        # Randomly select questions based on calculated probabilities
        questions = np.random.choice(person_questions,
                                     p=probabilities,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)
