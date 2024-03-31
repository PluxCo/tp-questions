"""
Starting point for the service questions
"""
import logging

from api.api import app as flask_app
from db_connector import DBWorker
from generator.generators import SimpleGenerator
from generator.router import PersonRouter

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    DBWorker.init_db_file("sqlite:///data/data.db")

    # Schedule(lambda x: 0).from_settings().start()

    router = PersonRouter(SimpleGenerator())
    flask_app.run(host="0.0.0.0", debug=False, port=3000)
