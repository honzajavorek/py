import re
import itertools
from operator import itemgetter

from pythoncz.pages.jobs import geo, parsers


RE_COMPANY_NAME = re.compile(r'''
,?\s+(
    AG|GmbH|SE|Ltd\.?|ltd\.?|Inc\.?|inc\.?|s\.r\.o\.|a\.s\.
)$
''', re.VERBOSE)


def group_by_pagination(feeds):
    paginated = []
    not_paginaged = []

    for feed in feeds:
        url = feed['feed_url']
        bucket = paginated if is_url_paginated(url) else not_paginaged
        bucket.append(feed)

    return paginated, not_paginaged


def is_url_paginated(url):
    return '%p' in url


def paginate_url(url, page):
    if '%p' not in url:
        raise ValueError(f'URL {url} is is missing %p, cannot be paginated')
    return url.replace('%p', str(page))


# TODO

# def companies_from_jobs(jobs):
#     groups = {}

#     for job in jobs:
#         location = get_effective_location(job)
#         location_key = get_effective_location_key(location)

#         groups.setdefault(location_key, dict(location=location, companies={}))
#         companies = groups[location_key]['companies']

#         company_name = job['company_name']
#         company_key = get_company_key(company_name)
#         companies.setdefault(company_key, dict(name=company_name,
#                                                urls=set(), jobs_urls=set()))
#         companies[company_key]['urls'].add(job['url'])

#     return [
#         {
#             'location_raw': group['location'],
#             'companies': sorted([
#                 {'name': company['name'],
#                  'urls': list(company['urls'])}
#                 for company in group['companies'].values()
#             ], key=itemgetter('name'))
#         }
#         for group in groups.values()
#     ]


# def get_effective_location(job):
#     if job['is_remote']:
#         return dict(cs='na dálku', en='remote')

#     location = job['location']
#     region = location['region']
#     region_en = location.get('region_en', location['region'])
#     country = location['country']
#     country_en = location.get('country_en', location['country'])

#     if country == 'Česko':
#         if region:
#             return dict(cs=region, en=region_en)
#         return dict(cs='celé Česko', en='anywhere in Czechia')
#     return dict(cs=country, en=country_en)


# def stats_from_jobs(jobs):
#     feeds = {}
#     companies = set()

#     remote_companies = set()
#     remote_jobs_count = 0

#     czech_companies = set()
#     czech_jobs_count = 0

#     non_czech_companies = set()
#     non_czech_jobs_count = 0

#     for job in jobs:
#         feed_id = job['feed']['id']
#         feeds.setdefault(feed_id, {**job['feed']})
#         feeds[feed_id].setdefault('jobs_count', 0)
#         feeds[feed_id]['jobs_count'] += 1

#         companies.add(job['company_name'])

#         if job['is_remote']:
#             remote_jobs_count += 1
#             remote_companies.add(job['company_name'])

#     return {
#         'feeds': list(feeds.values()),
#         'companies_count': len(companies),
#         'jobs_count': len(jobs),
#         'remote_companies_count': len(remote_companies),
#         'remote_jobs_count': remote_jobs_count,
#         'czech_companies_count': len(czech_companies),
#         'czech_jobs_count': czech_jobs_count,
#         'non_czech_companies_count': len(non_czech_companies),
#         'non_czech_jobs_count': non_czech_jobs_count,
#     }


def get_jobs(feeds_jobs):
    return itertools.chain.from_iterable(
        (
            {
                **job,
                'feed': {
                    'name': feed['name'],
                    'id': feed['id'],
                    'url': feed['url'],
                }
            }
            for job in jobs
        )
        for feed, jobs in feeds_jobs
    )


def get_jobs_parser(feed_id):
    try:
        return getattr(parsers, feed_id).jobs_from_bytes
    except AttributeError:
        raise ValueError(f'There is no jobs adapter for {feed_id}')


def get_job_details_parser(feed_id):
    try:
        return getattr(parsers, feed_id).job_details_from_bytes
    except AttributeError:
        raise ValueError(f'There is no job details adapter for {feed_id}')


def is_relevant_job(job, agencies=None):
    return (
        job['company_name'] not in (agencies or [])
        and job.get('location') != 'out_of_scope'
    )


def get_company_id(company_name):
    return RE_COMPANY_NAME.sub('', company_name)


def parse_locations(jobs):
    return ({**job, 'location': geo.parse(job['location_raw'])}
            for job in jobs if not job.get('location'))


def add_company_ids(jobs):
    return (
        {**job, 'company_id': get_company_id(job['company_name'])}
        for job in jobs
    )
