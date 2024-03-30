import json

from flask_restful import Resource, reqparse
from sqlalchemy import select, update, delete, or_, desc, func

from api.utils import abort_if_doesnt_exist, view_parser
from core.answers import Record
from core.questions import Question, QuestionGroupAssociation, QuestionType
from db_connector import DBWorker

# Request parser for updating question data
update_data_parser = reqparse.RequestParser()
update_data_parser.add_argument('text', type=str, required=False)
update_data_parser.add_argument('subject', type=str, required=False)
update_data_parser.add_argument('options', type=str, required=False, action='append')
update_data_parser.add_argument('answer', type=str, required=False)
update_data_parser.add_argument('groups', type=str, required=False, action='append')
update_data_parser.add_argument('level', type=int, required=False)
update_data_parser.add_argument('article_url', type=str, required=False)
update_data_parser.add_argument('type', type=QuestionType, required=False)

# Request parser for creating a new question
create_data_parser = reqparse.RequestParser()
create_data_parser.add_argument('text', type=str, required=True)
create_data_parser.add_argument('subject', type=str, required=False)
create_data_parser.add_argument('options', type=str, required=False, action='append')
create_data_parser.add_argument('answer', type=str, required=True)
create_data_parser.add_argument('groups', type=str, required=True, action='append')
create_data_parser.add_argument('level', type=int, required=True)
create_data_parser.add_argument('article_url', type=str, required=False)
create_data_parser.add_argument('type', type=QuestionType, required=False)

sorted_question_data_parser = view_parser.copy()
sorted_question_data_parser.add_argument('search_string', type=str, required=False, location="args", default="")


class QuestionResource(Resource):
    """
    Resource for handling individual Question instances.
    """

    @abort_if_doesnt_exist("question_id", Question)
    def get(self, question_id):
        """
        Get the details of a specific Question.

        Args:
            question_id (int): The ID of the Question.

        Returns:
            tuple: A tuple containing the details of the Question and HTTP status code.
        """
        with DBWorker() as db:
            # Retrieve the Question from the database and convert it to a dictionary
            db_question = db.get(Question, question_id).to_dict(rules=("-groups.id", "-groups.question_id"))

        return db_question, 200

    @abort_if_doesnt_exist("question_id", Question)
    def patch(self, question_id):
        # TODO: fix update of questions so that after changing options the answers stay correct.
        """
        Update the details of a specific Question.

        Args:
            question_id (int): The ID of the Question.

        Returns:
            tuple: A tuple containing the updated details of the Question and HTTP status code.
        """
        args = update_data_parser.parse_args()
        filtered_args = {k: v for k, v in args.items() if v is not None}

        if "options" in filtered_args:
            filtered_args["options"] = json.dumps(filtered_args["options"], ensure_ascii=True)

        groups = []
        if "groups" in filtered_args:
            groups = [QuestionGroupAssociation(question_id=question_id, group_id=g_id)
                      for g_id in filtered_args["groups"]]
            del filtered_args["groups"]

        with DBWorker() as db:
            db_question = db.get(Question, question_id)

            db.execute(update(Question).
                       where(Question.id == question_id).
                       values(filtered_args))

            if groups:
                db.execute(delete(QuestionGroupAssociation).
                           where(QuestionGroupAssociation.question_id == question_id))

                db_question.groups.extend(groups)

            if "options" in filtered_args or "answer" in filtered_args:
                answers_to_update = db.scalars(select(Record).where(Record.question_id == db_question.id))
                for answer in answers_to_update:
                    answer.calculate_points()

            db.commit()

        return self.get(question_id=question_id), 200

    def delete(self, question_id):
        with DBWorker() as db:
            question = db.get(Question, question_id)
            db.delete(question)
            db.commit()
        return '', 200


class QuestionsListResource(Resource):
    """
    Resource for handling lists of Question instances.
    """

    def get(self, **kwargs):
        """
        Get a list of Question instances.

        Returns:
            tuple: A tuple containing the list of Question instances and HTTP status code.
        """
        args = sorted_question_data_parser.parse_args()

        search_string = args['search_string']

        with DBWorker() as db:
            total = db.scalar(select(func.count(Question.id)))

            db_req = (select(Question, func.count(Question.id).over())
                      .where(or_(Question.text.ilike(f"%{search_string}%"),
                                 Question.subject.ilike(f"%{search_string}%"),
                                 Question.level.ilike(f"%{search_string}%"),
                                 Question.article_url.ilike(f"%{search_string}%"))))

            db_req = (db_req.order_by(args["orderBy"] if args["order"] == "asc" else desc(args["orderBy"]))
                      .limit(args["resultsCount"])
                      .offset(args["offset"]))

            questions = []
            results_filtered = 0
            for a, results_filtered in db.execute(db_req):
                questions.append(a.to_dict(rules=("-groups.id", "-groups.question_id")))

        return {"results_total": total, "results_count": results_filtered, "questions": questions}, 200

    def post(self, **kwargs):
        """
        Create a new Question instance.

        Returns:
            tuple: A tuple containing the details of the created Question and HTTP status code.
        """
        with DBWorker() as db:
            args = create_data_parser.parse_args()
            db_question = Question(text=args['text'],
                                   subject=args['subject'],
                                   answer=args['answer'],
                                   level=args['level'],
                                   article_url=args['article_url'])
            db.add(db_question)
            db.commit()

            for group in args['groups']:
                db_question.groups.append(QuestionGroupAssociation(question_id=db_question.id,
                                                                   group_id=group))
            db.commit()

            return QuestionResource().get(question_id=db_question.id)
