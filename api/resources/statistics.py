"""
File that contains the statistics resource.
"""
import logging

from flask_restful import Resource, reqparse
from sqlalchemy import select, distinct, func, case

from core.answers import Record, AnswerState
from core.questions import Question, QuestionGroupAssociation
from db_connector import DBWorker
from users import Person

question_stats_data_parser = reqparse.RequestParser()
question_stats_data_parser.add_argument('question_id', type=str, required=False)
question_stats_data_parser.add_argument('person_id', type=str, required=False)

logger = logging.getLogger(__name__)


class ShortStatisticsResource(Resource):

    @staticmethod
    def get():
        """

        :return:
        """
        logger.debug("Getting short statistics...")
        try:
            with DBWorker() as db:
                persons = Person.get_all_people()
                resp = {}

                for person in persons:
                    all_questions = db.scalars(select(Question).
                                               join(Question.groups).
                                               where(
                        QuestionGroupAssociation.group_id.in_(pg for pg, pl in person.groups)).
                                               group_by(Question.id)).all()

                    last_answers = (select(Record.id)
                                    .where(Record.person_id == person.id)
                                    .group_by(Record.question_id)
                                    .having(Record.answer_time == func.max(Record.answer_time)))

                    correct_count = db.scalar(select(func.sum(Record.points)).
                                              where(Record.id.in_(last_answers)))
                    answered_count = db.scalar(select(func.count(Record.id)).
                                               where(Record.id.in_(last_answers)))
                    questions_count = len(all_questions)

                    resp[person.id] = {"correct_count": correct_count,
                                       "answered_count": answered_count,
                                       "questions_count": questions_count}
            logger.debug("Returning statistics for all questions")
            return resp, 200
        except Exception as e:
            logger.error(e)
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500


# noinspection Style,Annotator
class UserStatisticsResource(Resource):
    @staticmethod
    def get(person_id):
        """

        :param person_id:
        :return:
        """
        person = Person.get_person(person_id)
        logger.debug(f"Returning statistics for person {person_id}...")
        try:
            with DBWorker() as db:
                last_user_answers = (select(Record.id)
                                     .where(Record.person_id == person.id)
                                     .group_by(Record.question_id)
                                     .having(Record.answer_time == func.max(Record.answer_time)))

                total_points, total_answered_count = db.execute(select(func.sum(Record.points),
                                                                       func.count(Record.question_id))
                                                                .where(Record.id.in_(last_user_answers))).one()

                # points and answered_count by subjects and levels
                level_subject_info = db.execute(select(Question.level,
                                                       Question.subject,
                                                       func.sum(Record.points),
                                                       func.count(Record.question_id))
                                                .join(Record.question)
                                                .where(Record.id.in_(last_user_answers))
                                                .group_by(Question.level, Question.subject)).all()

                questions_count = db.execute(select(Question.level, Question.subject, func.count(distinct(Question.id)))
                                             .join(Question.groups)
                                             .where(
                    QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups))
                                             .group_by(Question.level, Question.subject)).all()

                user_question_ids = (select(distinct(Question.id))
                                     .join(Question.groups)
                                     .where(QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups)))

                # contains total/last points and answered/transferred counts for all questions that available for user
                questions = db.execute(select(Question,
                                              func.coalesce(func.sum(Record.points), 0),
                                              func.count(case((Record.state == AnswerState.ANSWERED, 1))),
                                              func.count(case((Record.state == AnswerState.TRANSFERRED, 1))),
                                              func.coalesce(
                                                  case((Record.answer_time == func.max(Record.answer_time),
                                                        Record.points)), 0)
                                              )
                                       .outerjoin(Record, Question.id == Record.question_id)
                                       .where((Record.person_id == person_id) | (Record.person_id is None),
                                              Question.id.in_(user_question_ids))
                                       .group_by(Question.id)).all()

                ls_stat = [{"level": level,
                            "subject": subj,
                            "points": points,
                            "answered_count": count,
                            "questions_count": next(q_c for q_l, q_s, q_c in questions_count
                                                    if q_l == level and q_s == subj)}  # that's lmao find O(N^2)
                           for level, subj, points, count in level_subject_info]

                questions_stat = [{"question": q.to_dict(only=("id", "text", "subject", "level")),
                                   "total_points": total_points,
                                   "last_points": last_points,
                                   "answered_count": answered_count,
                                   "transferred_count": transferred_count}
                                  for q, total_points, answered_count, transferred_count, last_points in questions]

            resp = {"ls": ls_stat,
                    "questions": questions_stat,
                    "total_point": total_points,
                    "total_answered_count": total_answered_count}
            logger.debug("Returning user statistics")
            return resp, 200
        except Exception as e:
            logger.error(e)
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500
