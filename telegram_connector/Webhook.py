import logging

from flask_restful import Resource, reqparse

from telegram_connector.TelegramMessageFactory import TelegramMessageFactory


class Webhook(Resource):
    """
        Resource for handling incoming webhook requests from TelegramService.
        """

    # Request parser for handling incoming answer data
    # type - reply, request
    # data - {'answer': {'reply_to': 'message-id', 'data': 'text-of-the-answer-or-button-id'}, 'user_id': 'user-id'}

    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("type", type=dict, required=True)
    answer_parser.add_argument("data", type=dict, required=True)
    _factory: TelegramMessageFactory = None

    def post(self):
        """
        Handle incoming POST requests from TelegramService.
        """
        args = self.answer_parser.parse_args()
        logging.debug(f"Received answer request {args}")

        match args['type']:
            case "message":
                self._factory.response_handler(args['data'])
            case "request":
                self._factory.request_delivery(args['data']['user_id'])

        return {"clear_buttons": True}, 200
