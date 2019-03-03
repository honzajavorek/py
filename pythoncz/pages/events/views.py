from pathlib import Path

import arrow
from flask import Response, render_template, jsonify

from pythoncz import app
from pythoncz.data import load_data
from pythoncz.pages.events import events_to_ics_text, is_within_three_months


events_data_path = Path(__file__).parent / 'events_data.json'


@app.route('/events/')
def events():
    events = load_data(events_data_path, [], debug=app.debug)
    events = filter(is_within_three_months(arrow.utcnow()), events)
    return render_template('events.html', events=events)


@app.route('/events.ics')
def events_ics():
    events = load_data(events_data_path, [], debug=app.debug)
    events = filter(is_within_three_months(arrow.utcnow()), events)
    return Response(events_to_ics_text(events), mimetype='text/calendar')


@app.route('/events.json')
def events_json():
    events = load_data(events_data_path, [], debug=app.debug)
    events = filter(is_within_three_months(arrow.utcnow()), events)
    return jsonify(list(events))
