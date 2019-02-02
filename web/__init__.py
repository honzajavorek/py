import json
import logging
from pathlib import Path

from flask import Flask, render_template


DATA_DIR = Path(__file__).parent.parent / 'data'


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/events/')
def events():
    data_path = DATA_DIR / 'events' / 'data.json'
    try:
        events = json.loads(data_path.read_text())
    except FileNotFoundError:
        if app.debug:
            logging.warning((
                "There is no data in '%s'. "
                "Run 'pipenv run data.events' and retry the request to see content"
            ), data_path)
            events = []
        else:
            raise
    return render_template('events.html', events=events)
