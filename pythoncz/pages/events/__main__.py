from pathlib import Path

import requests
import yaml

from pythoncz.data import save_data
from pythoncz.pages.events import (sort_events, get_events,
                                   ics_events_from_text)


def download_ics_as_text(ics_url):
    try:
        response = requests.get(ics_url)
        response.raise_for_status()
        return response.text
    except Exception as request_exc:
        exc = RuntimeError(f'Could not get iCalendar feed from {ics_url}')
        raise exc from request_exc


config_path = Path(__file__).parent / 'config.yml'
config = yaml.safe_load(config_path.read_text())

events = sort_events(get_events(
    (feed, ics_events_from_text(download_ics_as_text(feed['ics_url'])))
    for feed in config['feeds']
))

data_path = Path(__file__).parent / 'events_data.json'
save_data(data_path, list(events))
