import time
from datetime import datetime
from pathlib import Path

import arrow
import pytest

from pythoncz.pages import articles


class Entry:
    def __init__(self, title=None, published_parsed=None, link=None):
        self.title = title
        self.published_parsed = published_parsed
        self.link = link


@pytest.fixture
def rss_bytes():
    return (Path(__file__).parent / 'feed.xml').read_bytes()


def feed():
    return {
        'title': 'Zprávičky o Pythonu na Root.cz',
        'url': 'http://example.com',
        'rss_url': 'http://example.com/feed.xml',
    }


@pytest.fixture(name='feed')
def feed_fixture():
    return feed()


def rss_entry():
    return Entry(
        title='Kritická zranitelnost v NumPy',
        published_parsed=time.gmtime(1551955579),
        link='http://example.com',
    )


@pytest.fixture(name='rss_entry')
def rss_entry_fixture():
    return rss_entry()


def test_sort_articles():
    sorted_articles = articles.sort_articles([
        {'date': arrow.get('2019-12-24')},
        {'date': arrow.get('2019-08-30')},
        {'date': arrow.get('2019-01-22')},
    ])

    assert sorted_articles == [
        {'date': arrow.get('2019-12-24')},
        {'date': arrow.get('2019-08-30')},
        {'date': arrow.get('2019-01-22')},
    ]


def test_get_articles_from_feeds():
    feed1 = feed()
    feed1['title'] = 'Python v ČR bloguje'
    rss_entry1 = rss_entry()
    rss_entry1.title = 'Článek o PyCon CZ'
    rss_entry2 = rss_entry()
    rss_entry2.title = 'Článek o PyLadies'

    feed2 = feed()
    feed2['title'] = 'Články o Pythonu na Root.cz'
    rss_entry3 = rss_entry()
    rss_entry3.title = 'Kritická zranitelnost v requests'

    feeds_rss_entries = [
        (feed1, [rss_entry1, rss_entry2]),
        (feed2, [rss_entry3]),
    ]

    assert list(articles.get_articles_from_feeds(feeds_rss_entries)) == [
        articles.rss_entry_to_article(feed1, rss_entry1),
        articles.rss_entry_to_article(feed1, rss_entry2),
        articles.rss_entry_to_article(feed2, rss_entry3),
    ]


def test_rss_entry_to_article(feed, rss_entry):
    article = articles.rss_entry_to_article(feed, rss_entry)

    assert article == {
        'title': 'Kritická zranitelnost v NumPy',
        'date': arrow.Arrow.utcfromtimestamp(1551955579),
        'url': 'http://example.com',
        'feed': {
            'title': 'Zprávičky o Pythonu na Root.cz',
            'url': 'http://example.com',
            'rss_url': 'http://example.com/feed.xml',
        }
    }


def test_config_article_to_article():
    article = articles.config_article_to_article({
        'title': 'A letter to the Python community in Africa',
        'date': '2019-01-17',
        'url': 'http://example.com',
    })

    assert article['title'] == 'A letter to the Python community in Africa'
    assert article['date'] == arrow.get(datetime(2019, 1, 17), 'UTC')
    assert article['url'] == 'http://example.com'


def test_rss_entries_from_bytes(rss_bytes):
    rss_entries = articles.rss_entries_from_bytes(rss_bytes)

    assert rss_entries[0].title == 'Title 1'
    assert rss_entries[0].published_parsed == time.gmtime(1550844000)
    assert rss_entries[0].link == 'http://example.com/1.html'

    assert rss_entries[1].title == 'Title 2'
    assert rss_entries[1].published_parsed == time.gmtime(1550595600)
    assert rss_entries[1].link == 'http://example.com/2.html'
