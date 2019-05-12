import itertools
import functools
from pathlib import Path

import requests
import yaml
import geocoder
from unidecode import unidecode

from pythoncz import log
from pythoncz.data import save_data
from pythoncz.pages.jobs import (get_jobs, jobs_from_bytes, stats_from_jobs,
                                 companies_from_jobs, group_by_pagination,
                                 paginate_url, get_job_details_parser,
                                 parse_geocode_result, embed_location_data,
                                 is_relevant_job)


logger = log.get('pythoncz.pages.jobs')


def download_as_bytes(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def download_feed(feed):
    url = feed['feed_url']
    try:
        logger.info(f"Downloading {url}")
        response_bytes = download_as_bytes(url)
    except Exception as request_exc:
        exc = RuntimeError(f'Could not get jobs feed from {url}')
        raise exc from request_exc
    return jobs_from_bytes(feed['id'], response_bytes, url)


def download_feed_paginated(feed):
    page = 1
    while True:
        url = paginate_url(feed['feed_url'], page)
        try:
            logger.info(f"Downloading {url}")
            response_bytes = download_as_bytes(url)
        except requests.HTTPError:
            break
        except Exception as request_exc:
            exc = RuntimeError(f'Could not get jobs feed from {url}')
            raise exc from request_exc

        jobs = list(jobs_from_bytes(feed['id'], response_bytes, url))
        if not jobs:
            break
        yield from jobs
        page += 1


def download_job_details(job):
    try:
        job_details_from_bytes = get_job_details_parser(job['feed']['id'])
    except ValueError:
        yield job
    else:
        url = job['url']
        try:
            logger.info(f"Downloading {url}")
            response_bytes = download_as_bytes(url)
        except Exception as request_exc:
            exc = RuntimeError(f'Could not get job details from {url}')
            raise exc from request_exc

        for job_details in job_details_from_bytes(response_bytes, url):
            yield {**job, **job_details}


@functools.lru_cache()
def geocode(text):
    text_ascii = unidecode(text)

    result = geocoder.google(text_ascii, language='cs', region='cz')
    region, country = parse_geocode_result(result)

    if ',' in text and not region:
        result = geocoder.google(result.latlng, method='reverse',
                                 language='cs', region='cz')
        region, country = parse_geocode_result(result)

    if country == 'Česko':
        return dict(region=region, country=country)

    result_en = geocoder.google(result.latlng, method='reverse',
                                language='en', region='cz')
    region_en, country_en = parse_geocode_result(result_en)
    return dict(region=region, region_en=region_en,
                country=country, country_en=country_en)


def geocode_job_location(job):
    if job['location']:
        return embed_location_data(job, geocode(job['location']))
    return job


def is_relevant_job_with_logging(job, agencies):
    is_relevant = is_relevant_job(job, agencies)
    if not is_relevant:
        logger.info(f"Skipping {job['url']}"
                    f" ({job['company_name']} @ {job['location']})")
    return is_relevant


config_path = Path(__file__).parent / 'config.yml'
config = yaml.safe_load(config_path.read_text())


paginated_feeds, not_paginaged_feeds = group_by_pagination(config['feeds'])
paginated_feeds_jobs = (
    (feed, download_feed_paginated(feed))
    for feed in paginated_feeds
)
not_paginaged_feeds_jobs = (
    (feed, download_feed(feed))
    for feed in not_paginaged_feeds
)


feeds_jobs = itertools.chain(paginated_feeds_jobs, not_paginaged_feeds_jobs)
jobs = (job for job in get_jobs(feeds_jobs)
        if is_relevant_job_with_logging(job, config['agencies']))
jobs = itertools.chain.from_iterable(map(download_job_details, jobs))
jobs = list(map(geocode_job_location, jobs))


data_path = Path(__file__).parent / 'jobs_data.json'
save_data(data_path, jobs)

data_path = Path(__file__).parent / 'stats_data.json'
save_data(data_path, stats_from_jobs(jobs))

data_path = Path(__file__).parent / 'companies_data.json'
save_data(data_path, companies_from_jobs(jobs))
