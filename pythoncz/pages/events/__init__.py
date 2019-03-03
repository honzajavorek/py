import re
import itertools
import operator

import ics


def sort_events(events):
    return sorted(events, key=operator.itemgetter('begins_at'))


def get_events(feeds_ics_events):
    return itertools.chain.from_iterable(
        (ics_event_to_event(feed, ics_event) for ics_event in ics_events)
        for feed, ics_events in feeds_ics_events
    )


def ics_event_to_event(feed, ics_event):
    return {
        'id': ics_event.uid,
        'name': ics_event.name or None,
        'description': ics_event.description or None,
        'location': ics_event.location or None,
        'url': get_ics_event_url(ics_event),
        'begins_at': ics_event.begin,
        'is_tentative': 'tentative-date' in ics_event.categories,
        'feed': {
            'name': feed['name'],
            'url': feed['url'],
            'ics_url': feed['ics_url'],
        },
    }


def get_ics_event_url(ics_event):
    return ics_event.url or find_first_url(ics_event.description)


def find_first_url(text):
    match = re.search(r'https?://\S+', text or '')
    if match:
        return match.group(0)
    return None


def ics_events_from_text(ics_text):
    return ics.Calendar(skip_valarm_lines(ics_text.splitlines())).events


def skip_valarm_lines(ics_text_lines):
    """
    Removes VALARM from the iCalendar file as in Google Calendar feeds it can
    contain invalid elements ACTION:NONE and we don't it in our data.
    """
    inside_valarm = False

    for line in ics_text_lines:
        if inside_valarm:
            inside_valarm = line != 'END:VALARM'
        else:
            inside_valarm = line == 'BEGIN:VALARM'
            if not inside_valarm:
                yield line


def events_to_ics_text(events):
    ics_events = map(event_to_ics_event, events)
    return ''.join(ics.Calendar(events=ics_events))


def event_to_ics_event(event):
    return ics.Event(
        uid=event['id'],
        name=event['name'],
        description=event['description'],
        location=event['location'],
        url=event['url'],
        begin=event['begins_at'],
        categories=(['tentative-date'] if event['is_tentative'] else []),
    )


def is_within_three_months(now_dt):
    in_three_months_dt = now_dt.replace(months=+3)

    def predicate(event):
        return now_dt <= event['begins_at'] <= in_three_months_dt
    return predicate
