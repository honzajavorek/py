import itertools
import operator
from time import mktime
from datetime import datetime

import arrow
import feedparser


def sort_articles(articles):
    return sorted(articles, key=operator.itemgetter('date'), reverse=True)


def get_articles_from_feeds(feeds_rss_entries):
    return itertools.chain.from_iterable(
        (rss_entry_to_article(feed, rss_entry) for rss_entry in rss_entries)
        for feed, rss_entries in feeds_rss_entries
    )


def rss_entry_to_article(feed, rss_entry):
    return {
        'title': rss_entry.title,
        'date': arrow.get(
            datetime.fromtimestamp(mktime(rss_entry.published_parsed))
        ),
        'url': rss_entry.link,
        'feed': {
            'title': feed['title'],
            'url': feed['url'],
            'rss_url': feed['rss_url'],
        }
    }


def config_article_to_article(config_article):
    return {
        'title': config_article['title'],
        'date': arrow.get(config_article['date']),
        'url': config_article['url'],
    }


def rss_entries_from_bytes(rss_bytes):
    return feedparser.parse(rss_bytes).entries
