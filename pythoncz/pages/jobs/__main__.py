import os
import itertools
from pathlib import Path

import requests
import yaml

from pythoncz import log
from pythoncz.data import save_data
from pythoncz.pages.jobs import (geo, get_jobs, get_jobs_parser,
                                 # stats_from_jobs, companies_from_jobs,
                                 group_by_pagination, paginate_url,
                                 get_job_details_parser, is_relevant_job,
                                 add_company_ids, parse_locations)


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
    jobs_from_bytes = get_jobs_parser(feed['id'])
    yield from jobs_from_bytes(response_bytes, url)


def download_feed_paginated(feed):
    page = 1
    while True:
        url = paginate_url(feed['feed_url'], page)
        try:
            logger.info(f"Downloading {url}")
            response_bytes = download_as_bytes(url)
        except requests.HTTPError:
            break
        except Exception as exc:
            exc = RuntimeError(f'Could not get jobs feed from {url}')
            raise exc from exc

        jobs_from_bytes = get_jobs_parser(feed['id'])
        jobs = list(jobs_from_bytes(response_bytes, url))
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
        except Exception:
            # Some jobs are expired and their detail doesn't load even though
            # they're listed in APIs, exports, search results
            logger.exception('Could not get job details from {url}')
            yield job
        else:
            for job_details in job_details_from_bytes(response_bytes, url):
                yield {**job, **job_details}


def download_details(jobs):
    return itertools.chain.from_iterable(map(download_job_details, jobs))


def is_relevant_job_with_logging(job, agencies=None):
    is_relevant = is_relevant_job(job, agencies)
    if not is_relevant:
        logger.info(f"Skipping {job['url']}"
                    f" ({job['company_name']} @ {job['location_raw']})")
    return is_relevant


def keep_relevant_jobs(jobs, agencies=None):
    return (job for job in jobs
            if is_relevant_job_with_logging(job, agencies))


def geocode_locations(jobs, api_key=None):
    return (
        {**job,
         'location': (
             job.get('location')
             or geo.resolve(job['location_raw'], api_key=api_key)
         )}
        for job in jobs
    )


config_path = Path(__file__).parent / 'config.yml'
config = yaml.safe_load(config_path.read_text())

google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    raise ValueError('Environment variable GOOGLE_API_KEY is not set')


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
jobs = get_jobs(feeds_jobs)


# Running keep_relevant_jobs() after every change in data as it is a cheap
# operation which can significantly lower the number of expensive operations
# needed in further steps.

jobs = keep_relevant_jobs(jobs, config['agencies'])
jobs = parse_locations(jobs)
jobs = keep_relevant_jobs(jobs)
jobs = download_details(jobs)
jobs = parse_locations(jobs)
jobs = keep_relevant_jobs(jobs)
jobs = geocode_locations(jobs, api_key=google_api_key)
jobs = keep_relevant_jobs(jobs)
jobs = add_company_ids(jobs)
jobs = list(jobs)


data_path = Path(__file__).parent / 'jobs_data.json'
save_data(data_path, jobs)

# TODO

# data_path = Path(__file__).parent / 'stats_data.json'
# save_data(data_path, stats_from_jobs(jobs))

# data_path = Path(__file__).parent / 'companies_data.json'
# save_data(data_path, companies_from_jobs(jobs))
