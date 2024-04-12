"""
This module provides the API for the question service
"""
from flask import Flask
from flask_restful import Api

from api.resources.answer import RecordResource, RecordCreationResource, RecordSearchResource
from api.resources.questions import QuestionResource, QuestionCreationResource, QuestionSearchResource
from api.resources.statistics import ShortStatisticsResource, UserStatisticsResource
from telegram_connector.webhook import Webhook

app = Flask(__name__)
api = Api(app)

api.add_resource(QuestionResource, '/question/<int:question_id>')
api.add_resource(QuestionCreationResource, '/question/')
api.add_resource(QuestionSearchResource, '/question/search/')

api.add_resource(RecordResource, "/record/<int:record_id>")
api.add_resource(RecordCreationResource, "/record/")
api.add_resource(RecordSearchResource, "/record/search/")

api.add_resource(ShortStatisticsResource, "/statistics/user_short")
api.add_resource(UserStatisticsResource, "/statistics/user/<string:person_id>")

api.add_resource(Webhook, "/webhook/")
