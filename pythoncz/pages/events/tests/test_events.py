import re
from pathlib import Path

import arrow
from ics import Event
import pytest

from pythoncz.pages import events


@pytest.fixture
def ics_text_with_valarm():
    return (Path(__file__).parent / 'with_valarm.ics').read_text()


@pytest.fixture
def ics_text_without_valarm():
    return (Path(__file__).parent / 'without_valarm.ics').read_text()


def feed():
    return {
        'name': 'Czech Python Events',
        'url': 'http://example.com',
        'ics_url': 'http://example.com/feed.ics',
    }


@pytest.fixture(name='feed')
def feed_fixture():
    return feed()


def ics_event():
    ics_event = Event()
    ics_event.uid = '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com'
    ics_event.name = 'Sprint na východě'
    ics_event.description = 'popis'
    ics_event.location = 'Lískovec'
    ics_event.url = 'http://example.com'
    ics_event.begin = arrow.get('2018-04-04T00:00:00')
    ics_event.categories = set()
    return ics_event


@pytest.fixture(name='ics_event')
def ics_event_fixture():
    return ics_event()


def test_skip_valarm_lines(ics_text_with_valarm, ics_text_without_valarm):
    ics_text_lines = ics_text_with_valarm.splitlines()
    ics_text_lines = list(events.skip_valarm_lines(ics_text_lines))

    assert ics_text_lines == ics_text_without_valarm.splitlines()


def test_ics_events_from_text(ics_text_with_valarm):
    ics_events = events.ics_events_from_text(ics_text_with_valarm)

    assert len(ics_events) == 1

    ics_event = ics_events[0]

    assert ics_event.uid == '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com'
    assert ics_event.name == 'Sprint na východě'
    assert ics_event.description == ''
    assert ics_event.location == 'Lískovec'
    assert ics_event.url is None
    assert ics_event.begin == arrow.get('2018-04-04')
    assert ics_event.categories == set()


def test_events_to_ics_text():
    ics_text = events.events_to_ics_text([{
        'id': '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com',
        'name': 'Sprint na východě',
        'description': None,
        'location': 'Lískovec',
        'url': 'http://example.com',
        'begins_at': arrow.get('2018-04-04T00:00:00'),
        'is_tentative': False,
    }])

    expected_ics_text = '\r\n'.join([
        'BEGIN:VCALENDAR',
        'PRODID:ics.py - http://git.io/lLljaA',
        'VERSION:2.0',
        'BEGIN:VEVENT',
        'DTSTAMP:XXXXXXXXXXXXXXXX',
        'DTSTART:20180404T000000Z',
        'SUMMARY:Sprint na východě',
        'LOCATION:Lískovec',
        'URL:http://example.com',
        'TRANSP:OPAQUE',
        'UID:65jd6rs6vb3h0hh0ofn1dvlgaj@google.com',
        'END:VEVENT',
        'END:VCALENDAR',
    ]) + '\n'

    ics_text = re.sub(r'DTSTAMP:[\dTZ]+', 'DTSTAMP:XXXXXXXXXXXXXXXX', ics_text)
    assert ics_text == expected_ics_text


def test_events_to_ics_text_multiple():
    ics_text = events.events_to_ics_text([
        {
            'id': 'abc@google.com',
            'name': 'Sprint na východě',
            'description': None,
            'location': None,
            'url': None,
            'begins_at': arrow.get('2018-04-04T00:00:00'),
            'is_tentative': False,
        },
        {
            'id': 'xyz@google.com',
            'name': 'Sprint na západě',
            'description': None,
            'location': None,
            'url': None,
            'begins_at': arrow.get('2018-05-05T00:00:00'),
            'is_tentative': False,
        },
    ])

    assert ics_text.count('BEGIN:VEVENT') == 2
    assert ics_text.count('END:VEVENT') == 2


@pytest.mark.parametrize('is_tentative,expected_categories', [
    (True, ['tentative-date']),
    (False, []),
])
def test_event_to_ics_event(is_tentative, expected_categories):
    ics_event = events.event_to_ics_event({
        'id': '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com',
        'name': 'Sprint na východě',
        'description': None,
        'location': 'Lískovec',
        'url': 'http://example.com',
        'begins_at': arrow.get('2018-04-04T00:00:00'),
        'is_tentative': is_tentative,
    })

    assert ics_event.uid == '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com'
    assert ics_event.name == 'Sprint na východě'
    assert ics_event.description is None
    assert ics_event.location == 'Lískovec'
    assert ics_event.url == 'http://example.com'
    assert ics_event.begin == arrow.get('2018-04-04T00:00:00')
    assert ics_event.categories == set(expected_categories)


@pytest.mark.parametrize('text,expected', [
    (None, None),
    ('', None),
    ('lorem ipsum dolor sit amet', None),
    ('https://python.cz', 'https://python.cz'),
    ('http://python.cz', 'http://python.cz'),
    ('lorem ipsum https://python.cz dolor sit amet', 'https://python.cz'),
    ('lorem https://python.cz ipsum https://pyvo.cz', 'https://python.cz'),
])
def test_find_first_url(text, expected):
    assert events.find_first_url(text) == expected


@pytest.mark.parametrize('event,expected_url', [
    (Event(), None),
    (Event(url='https://python.cz'), 'https://python.cz'),
    (Event(description='https://pyvo.cz', url='https://python.cz'),
     'https://python.cz'),
    (Event(description='https://pyvo.cz'), 'https://pyvo.cz'),
    (Event(description='''
        See: https://www.meetup.com/PyData-Prague/events/257775220

        Looking forward to see you!
     '''),
     'https://www.meetup.com/PyData-Prague/events/257775220'),
])
def test_get_ics_event_url(event, expected_url):
    assert events.get_ics_event_url(event) == expected_url


@pytest.mark.parametrize('begins_at,expected', [
    ('2019-08-29', False),
    ('2019-08-30', True),
    ('2019-09-30', True),
    ('2019-10-30', True),
    ('2019-11-30', True),
    ('2019-12-01', False),
])
def test_is_within_three_months(begins_at, expected):
    predicate = events.is_within_three_months(arrow.get('2019-08-30'))

    assert predicate({'begins_at': arrow.get(begins_at)}) is expected


def test_sort_events():
    sorted_events = events.sort_events([
        {'begins_at': arrow.get('2019-12-24')},
        {'begins_at': arrow.get('2019-08-30')},
        {'begins_at': arrow.get('2019-01-22')},
    ])

    assert sorted_events == [
        {'begins_at': arrow.get('2019-01-22')},
        {'begins_at': arrow.get('2019-08-30')},
        {'begins_at': arrow.get('2019-12-24')},
    ]


def test_ics_event_to_event(feed, ics_event):
    event = events.ics_event_to_event(feed, ics_event)

    assert event['id'] == '65jd6rs6vb3h0hh0ofn1dvlgaj@google.com'
    assert event['name'] == 'Sprint na východě'
    assert event['description'] == 'popis'
    assert event['location'] == 'Lískovec'
    assert event['url'] == 'http://example.com'
    assert event['begins_at'] == arrow.get('2018-04-04T00:00:00')
    assert event['is_tentative'] is False


def test_ics_event_to_event_tentative(feed, ics_event):
    ics_event.categories.add('tentative-date')
    event = events.ics_event_to_event(feed, ics_event)

    assert event['is_tentative'] is True


@pytest.mark.parametrize('empty_value', [None, ''])
def test_ics_event_to_event_optional(feed, ics_event, empty_value):
    ics_event.name = empty_value
    ics_event.description = empty_value
    ics_event.location = empty_value
    ics_event.url = empty_value
    event = events.ics_event_to_event(feed, ics_event)

    assert event['name'] is None
    assert event['description'] is None
    assert event['location'] is None
    assert event['url'] is None


def test_get_events():
    feed1 = feed()
    feed1['name'] = 'Pyvo'
    ics_event1 = ics_event()
    ics_event1.name = 'Pražské Pyvo: Machine Learning'
    ics_event2 = ics_event()
    ics_event2.name = 'Brněnské Pyvo: CLI'

    feed2 = feed()
    feed2['name'] = 'PyWorking'
    ics_event3 = ics_event()
    ics_event3.name = 'PyWorking Praha: API'

    feeds_ics_events = [
        (feed1, [ics_event1, ics_event2]),
        (feed2, [ics_event3]),
    ]

    assert list(events.get_events(feeds_ics_events)) == [
        events.ics_event_to_event(feed1, ics_event1),
        events.ics_event_to_event(feed1, ics_event2),
        events.ics_event_to_event(feed2, ics_event3),
    ]
