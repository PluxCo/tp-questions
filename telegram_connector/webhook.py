"""
Telegram Webhook resource which works with requests from other services.
"""
import logging

from flask_restful import Resource, reqparse

from telegram_connector.telegram_message_factory import TelegramMessageFactory


# noinspection Style,Annotator
class Webhook(Resource):
    """
    Resource for handling incoming webhook requests from TelegramService.
    """

    # Request parser for handling incoming answer data

    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("type", type=str, required=True)
    answer_parser.add_argument("session", type=dict, required=False)
    answer_parser.add_argument("feedback", type=dict, required=False)
    _factory: TelegramMessageFactory = None

    def post(self):
        """
        Handles incoming POST requests from TelegramService.
        """
        args = self.answer_parser.parse_args()
        try:
            match args['type']:
                case "FEEDBACK":
                    logging.debug(f"Received feedback {args}")
                    self._factory.response_handler(args['feedback'])
                    if args['session'] and args['session']['state'] == "OPEN":
                        self._factory.request_delivery(args['session']['user_id'])

                case "SESSION":
                    logging.debug(f"Received request {args}")
                    if args['session'] and args['session']['state'] == "OPEN":
                        self._factory.request_delivery(args['session']['user_id'])

            return "Handled Successfully", 200
        except Exception as e:
            logging.exception(e)
            return {"message": str(e)}, 400
