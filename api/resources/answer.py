import datetime

from flask_restful import Resource, reqparse
from sqlalchemy import select, desc, func, update

from api.utils import abort_if_doesnt_exist, view_parser
from core.answers import Record, AnswerState
from core.questions import QuestionType
from db_connector import DBWorker

# Request parser for filtering answer resources based on person_id and question_id
fields_parser = view_parser.copy()
fields_parser.add_argument('answer', type=dict, required=False, default={})

planned_answer_parser = reqparse.RequestParser()
planned_answer_parser.add_argument('person_id', type=str, required=True)
planned_answer_parser.add_argument('question_id', type=int, required=True)
planned_answer_parser.add_argument('ask_time', type=datetime.datetime.fromisoformat, required=True)

update_answer_parser = reqparse.RequestParser()
update_answer_parser.add_argument('points', type=float, required=False)
update_answer_parser.add_argument('state', type=AnswerState, required=False)


class AnswerResource(Resource):
    """
    Resource for handling individual Record instances.
    """

    @abort_if_doesnt_exist("answer_id", Record)
    def get(self, answer_id):
        """
        Get the details of a specific Record.

        Args:
            answer_id (int): The ID of the Record.

        Returns:
            tuple: A tuple containing the details of the Record and HTTP status code.
        """
        with DBWorker() as db:
            # Retrieve the Record from the database and convert it to a dictionary
            db_answer = db.get(Record, answer_id).to_dict(rules=("-question",))
        return db_answer, 200

    @abort_if_doesnt_exist("answer_id", Record)
    def delete(self, answer_id):
        with DBWorker() as db:
            answer = db.get(Record, answer_id)
            db.delete(answer)
            db.commit()
        return '', 200

    @abort_if_doesnt_exist("answer_id", Record)
    def patch(self, answer_id):
        args = {k: v for k, v in update_answer_parser.parse_args().items() if v is not None}

        with DBWorker() as db:
            db.execute(update(Record).where(Record.id == answer_id)
                       .values(**args))
            db.commit()

            db_answer = db.get(Record, answer_id).to_dict(rules=("-question",))
        return db_answer, 200


class AnswerListResource(Resource):
    """
    Resource for handling lists of Record instances.
    """

    def get(self):
        """
        Get a list of Record instances based on optional filtering parameters.

        Returns:
            tuple: A tuple containing the list of Record instances and HTTP status code.
        """
        # Parse the filtering parameters from the request
        args = fields_parser.parse_args()

        # TODO: add adequate parsers
        answer_filters = args["answer"]
        if "state" in answer_filters:
            answer_filters["state"] = AnswerState(answer_filters["state"])

        question_filters = answer_filters.pop("question", {})
        if "type" in question_filters:
            question_filters["type"] = QuestionType(question_filters["type"])

        with DBWorker() as db:
            # Retrieve Record instances from the database based on the filtering parameters
            db_req = (select(Record, func.count(Record.id).over())
                      .filter_by(**answer_filters))

            if question_filters:
                db_req = db_req.join(Record.question).filter_by(**question_filters)

            db_req = (db_req.order_by(args["orderBy"] if args["order"] == "asc" else desc(args["orderBy"]))
                      .limit(args["resultsCount"])
                      .offset(args["offset"]))

            answers = []
            results_total = 0
            for a, results_total in db.execute(db_req):
                answers.append(a.to_dict(rules=("-question",)))

        return {"results_total": results_total, "results_count": len(answers), "answers": answers}, 200

    def post(self):
        with DBWorker() as db:
            args = planned_answer_parser.parse_args()

            new_answer = Record(person_id=args['person_id'],
                                question_id=args['question_id'],
                                ask_time=args['ask_time'],
                                state=AnswerState.NOT_ANSWERED)

            db.add(new_answer)
            db.commit()

        return '', 200
