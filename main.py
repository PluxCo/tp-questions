import datetime
import logging

from api.api import app as flask_app
from db_connector import DBWorker
from tools import Settings

logging.basicConfig(level=logging.DEBUG)

default_settings = {
    "time_period": datetime.timedelta(seconds=30),
    "from_time": datetime.time(0),
    "to_time": datetime.time(23, 59),
    "week_days": [d for d in range(7)],
}

if __name__ == '__main__':
    Settings().setup("data/settings.stg", default_settings)
    DBWorker.init_db_file("data/database.db")

    # Schedule(lambda x: 0).from_settings().start()

    flask_app.run(host="0.0.0.0", debug=False, port=3000)
