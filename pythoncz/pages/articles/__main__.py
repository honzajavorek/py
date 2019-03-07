import itertools
from pathlib import Path

import requests
import yaml

from pythoncz.data import save_data
from pythoncz.pages.articles import (sort_articles, get_articles_from_feeds,
                                     rss_entries_from_bytes,
                                     config_article_to_article)


def download_rss_as_bytes(rss_url):
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
        return response.content
    except Exception as request_exc:
        exc = RuntimeError(f'Could not get RSS/Atom feed from {rss_url}')
        raise exc from request_exc


config_path = Path(__file__).parent / 'config.yml'
config = yaml.safe_load(config_path.read_text())

articles_from_feeds = get_articles_from_feeds(
    (feed, rss_entries_from_bytes(download_rss_as_bytes(feed['rss_url'])))
    for feed in config['feeds']
)
articles = sort_articles(itertools.chain(
    articles_from_feeds,
    map(config_article_to_article, config['articles']),
))

data_path = Path(__file__).parent / 'articles_data.json'
save_data(data_path, list(articles))
