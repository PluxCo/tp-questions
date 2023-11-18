from flask import Flask
from flask_restful import Api

from api.resources.answer import AnswerResource, AnswerListResource
from api.resources.questions import QuestionResource, QuestionsListResource
from api.resources.settings import SettingsResource

app = Flask(__name__)
api = Api(app)

api.add_resource(QuestionResource, '/question/<int:question_id>')
api.add_resource(QuestionsListResource, '/question/')
api.add_resource(AnswerResource, "/answer/<int:answer_id>")
api.add_resource(AnswerListResource, "/answer/")
api.add_resource(SettingsResource, "/settings/")
