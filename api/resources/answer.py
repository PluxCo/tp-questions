import datetime

from flask_restful import Resource, reqparse
from sqlalchemy import select, desc, func, update

from api.utils import abort_if_doesnt_exist, view_parser
from core.answers import Record, AnswerState, TestRecord, OpenRecord
from core.questions import Question
from db_connector import DBWorker

# Request parser for filtering answer resources based on person_id and question_id
fields_parser = view_parser.copy()
fields_parser.add_argument('record', type=dict, required=False, default={})

planned_answer_parser = reqparse.RequestParser()
planned_answer_parser.add_argument('person_id', type=str, required=True)
planned_answer_parser.add_argument('question_id', type=int, required=True)
planned_answer_parser.add_argument('ask_time', type=datetime.datetime.fromisoformat, required=True)

update_answer_parser = reqparse.RequestParser()
update_answer_parser.add_argument('points', type=float, required=False)
update_answer_parser.add_argument('state', type=AnswerState, required=False)


class RecordResource(Resource):
    """
    Resource for handling individual Record instances.
    """

    @abort_if_doesnt_exist("record_id", Record)
    def get(self, record_id):
        """
        Get the details of a specific Record.

        Args:
            record_id (int): The ID of the Record.

        Returns:
            tuple: A tuple containing the details of the Record and HTTP status code.
        """
        try:
            with DBWorker() as db:
                # Retrieve the Record from the database and convert it to a dictionary
                db_answer = db.get(Record, record_id).to_dict(rules=("-question",))
            return db_answer, 200
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500

    @abort_if_doesnt_exist("record_id", Record)
    def delete(self, record_id):
        try:
            with DBWorker() as db:
                record = db.get(Record, record_id)
                db.delete(record)
                db.commit()

            return {"message": "Record deleted successfully"}, 200
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500

    @abort_if_doesnt_exist("record_id", Record)
    def patch(self, record_id):
        try:
            args = {k: v for k, v in update_answer_parser.parse_args().items() if v is not None}

            with DBWorker() as db:
                db.execute(update(Record).where(Record.id == record_id).values(**args))
                db.commit()

                db_answer = db.get(Record, record_id)

                return db_answer.to_dict(rules=("-question",)), 200
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500


class RecordCreationResource(Resource):
    """
    Resource for handling lists of Record instances.
    """

    @staticmethod
    def _create_question_instance(args):
        """
        Create a new Record instance based on the provided arguments.

        Args:
            args (dict): Parsed arguments for creating a record.

        Returns:
            Record: Instance of the appropriate Record subclass.
        """
        with DBWorker() as db:
            question_type = db.get(Question, args['question_id']).type

        if question_type == 'TEST':
            return TestRecord(**args, state=AnswerState.NOT_ANSWERED)
        elif question_type == 'OPEN':
            return OpenRecord(**args, state=AnswerState.NOT_ANSWERED)
        else:
            raise ValueError("Invalid question type provided")

    def post(self):
        try:
            with DBWorker() as db:
                args = planned_answer_parser.parse_args()
                new_answer = self._create_question_instance(args)
                db.add(new_answer)
                db.commit()
            return {"message": "Record was planned successfully"}, 200
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500


class RecordSearchResource(Resource):
    def post(self):
        """
        Get a list of Record instances based on optional filtering parameters.

        Returns:
            tuple: A tuple containing the list of Record instances and HTTP status code.
        """
        try:
            # Parse the filtering parameters from the request
            args = fields_parser.parse_args()

            answer_filters = args.get("record")
            if "state" in answer_filters:
                answer_filters["state"] = AnswerState(answer_filters["state"])

            question_filters = answer_filters.pop("question", {})

            with DBWorker() as db:
                # Retrieve Record instances from the database based on the filtering parameters
                query = (select(Record, func.count(Record.id).over())
                         .filter_by(**answer_filters))

                if question_filters:
                    query = query.join(Record.question).filter_by(**question_filters)

                query = (query.order_by(args["orderBy"] if args["order"] == "asc" else desc(args["orderBy"]))
                         .limit(args["resultsCount"])
                         .offset(args["offset"]))

                records = []
                results_total = 0
                for record, results_total in db.execute(query):
                    records.append(record.to_dict(rules=("-question",)))

            return {"results_total": results_total, "results_count": len(records), "records": records}, 200
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}"}, 500
