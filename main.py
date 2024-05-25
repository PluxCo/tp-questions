"""
Starting point for the service questions
"""
import logging

from api.api import app as flask_app
from db_connector import DBWorker
from generator.generators import SmartGenerator
from generator.router import PersonRouter

logging.basicConfig(level=logging.INFO)
logging.getLogger("api").setLevel(logging.DEBUG)
logging.getLogger("generator").setLevel(logging.DEBUG)
logging.getLogger("telegram_connector").setLevel(logging.DEBUG)

if __name__ == '__main__':
    DBWorker.init_db_file("sqlite:///data/data.db")

    # Schedule(lambda x: 0).from_settings().start()

    router = PersonRouter(SmartGenerator())
    flask_app.run(host="0.0.0.0", debug=False, port=3000)
