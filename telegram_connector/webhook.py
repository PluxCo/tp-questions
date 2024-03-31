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
    # type - message, request
    # data - {'answer': {'reply_to': 'message-id', 'data': 'text-of-the-answer-or-button-id'}, 'user_id': 'user-id'}

    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("type", type=str, required=True)
    answer_parser.add_argument("data", type=dict, required=True)
    _factory: TelegramMessageFactory = None

    def post(self):
        """
        Handles incoming POST requests from TelegramService.
        """
        args = self.answer_parser.parse_args()
        try:
            match args['type']:
                case "message":
                    logging.debug(f"Received message {args}")
                    self._factory.response_handler(args['data'])
                case "request":
                    logging.debug(f"Received request {args}")
                    self._factory.request_delivery(args['data']['user_id'])

            return {"clear_buttons": True}, 200
        except Exception as e:
            logging.exception(e)
            return {"message": str(e)}, 500
