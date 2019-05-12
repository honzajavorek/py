import re
import json
import itertools
from operator import itemgetter

from slugify import slugify
from lxml import html, etree as xml


REMOTE_RE = re.compile(r'\b(remote|anywhere|externě)\b')
LOCATION_RE = re.compile(r'''
\b(
    česk|cesk|czech|praha|prague|brno|ostrava|
    slovensk|slovak|
    deutschland|germany|
    polska|poland|
    österreich|ȍsterreich|osterreich|austria
)
''', re.VERBOSE)
RE_COMPANY_NAME = re.compile(r'''
,?\s+(
    AG|GmbH|SE|Ltd\.?|ltd\.?|Inc\.?|inc\.?|s\.r\.o\.|a\.s\.
)$
''', re.VERBOSE)

WHITESPACE_RE = re.compile(r'\s+')
LEADING_PUNCTUATION_RE = re.compile(r'^[\-\|]\s+')


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


def companies_from_jobs(jobs):
    groups = {}

    for job in jobs:
        location = get_effective_location(job)
        location_key = get_effective_location_key(location)

        groups.setdefault(location_key, dict(location=location, companies={}))
        companies = groups[location_key]['companies']

        company_name = job['company_name']
        company_key = get_company_key(company_name)
        companies.setdefault(company_key, dict(name=company_name,
                                               urls=set(), jobs_urls=set()))
        companies[company_key]['urls'].add(job['url'])

    return [
        {
            'location': group['location'],
            'companies': sorted([
                {'name': company['name'],
                 'urls': list(company['urls'])}
                for company in group['companies'].values()
            ], key=itemgetter('name'))
        }
        for group in groups.values()
    ]


def get_effective_location(job):
    if job['is_remote']:
        return dict(cs='na dálku', en='remote')

    location = job['location']
    region = location['region']
    region_en = location.get('region_en', location['region'])
    country = location['country']
    country_en = location.get('country_en', location['country'])

    if country == 'Česko':
        if region:
            return dict(cs=region, en=region_en)
        return dict(cs='celé Česko', en='anywhere in Czechia')
    return dict(cs=country, en=country_en)


def get_effective_location_key(effective_location):
    return '{cs}###{en}'.format_map(effective_location)


def get_company_key(company_name):
    return RE_COMPANY_NAME.sub('', company_name)


def stats_from_jobs(jobs):
    feeds = {}
    companies = set()

    remote_companies = set()
    remote_jobs_count = 0

    czech_companies = set()
    czech_jobs_count = 0

    non_czech_companies = set()
    non_czech_jobs_count = 0

    for job in jobs:
        feed_id = job['feed']['id']
        feeds.setdefault(feed_id, {**job['feed']})
        feeds[feed_id].setdefault('jobs_count', 0)
        feeds[feed_id]['jobs_count'] += 1

        companies.add(job['company_name'])

        if job['is_remote']:
            remote_jobs_count += 1
            remote_companies.add(job['company_name'])

    return {
        'feeds': list(feeds.values()),
        'companies_count': len(companies),
        'jobs_count': len(jobs),
        'remote_companies_count': len(remote_companies),
        'remote_jobs_count': remote_jobs_count,
        'czech_companies_count': len(czech_companies),
        'czech_jobs_count': czech_jobs_count,
        'non_czech_companies_count': len(non_czech_companies),
        'non_czech_jobs_count': non_czech_jobs_count,
    }


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


def jobs_from_bytes(feed_id, *args):
    yield from {
        'jobscz': jobs_from_jobscz,
        'startupjobscz': jobs_from_startupjobscz,
        'stackoverflowcom': jobs_from_stackoverflowcom,
        'pythonorg': jobs_from_pythonorg,
        'remoteok': jobs_from_remoteok,
    }[feed_id](*args)


def get_job_details_parser(feed_id):
    try:
        return {
            'jobscz': job_details_from_jobscz,
            'startupjobscz': job_details_from_startupjobscz,
        }[feed_id]
    except KeyError:
        raise ValueError(f'There is no job details parser for {feed_id}')


def jobs_from_jobscz(response_bytes, base_url):
    elements = xml.fromstring(response_bytes)
    for job_element in elements.iterfind('.//position'):
        url = normalize_text(job_element.find('url').text)

        company_element = job_element.find('companyName')
        company_name = normalize_text(company_element.text)

        location_elements = job_element.iterfind('.//locality')
        locations = frozenset([normalize_text(l.text)
                               for l in location_elements])

        for location in locations:
            yield {
                'url': url,
                'is_remote': False,
                'is_relevant': True,
                'company_name': company_name,
                'company_url': None,
                'location': f'{company_name}, {location}, Česko',
            }


def job_details_from_jobscz(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    try:
        location_element = elements.cssselect('a[href*="mapy.cz"]')[0]
    except IndexError:
        yield {}
    else:
        location = normalize_text(location_element.text_content())
        yield {'location': f'{location}, Česko'}


def jobs_from_startupjobscz(response_bytes, base_url):
    elements = xml.fromstring(response_bytes)
    for job_element in elements.iterfind('.//offer'):
        url = normalize_text(job_element.find('url').text)

        company_element = job_element.find('startup')
        company_name = normalize_text(company_element.text)

        company_url_element = job_element.find('startupURL')
        company_url = normalize_text(company_url_element.text)

        yield {
            'url': url,
            'is_remote': None,
            'is_relevant': True,
            'company_name': company_name,
            'company_url': company_url,
            'location': None,
        }


# Czechia
# Praha, Praha 3
# Praha, Brno
# Liberec, Praha, Praha 2
# Česká republika, Praha 4
# Prague 6
def parse_startupjobscz_location(text):
    locations = filter(None, map(normalize_text, text.split(',')))
    locations = set([
        ('Praha' if loc.lower().startswith(('praha', 'prague')) else loc)
        for loc in locations
    ])
    locations = [
        f'{loc}, Česko' for loc in locations
        if loc.lower() not in ('czechia', 'česká republika')
    ]
    return locations or ['Česká republika']


def job_details_from_startupjobscz(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    elements.make_links_absolute(base_url)

    job_details_element = elements.cssselect('#offer-detail .details')[0]
    location_element, _, job_type_element = list(job_details_element)

    is_remote = looks_remote(job_type_element.text_content())

    if not is_remote:
        location_text = normalize_text(location_element.text_content())
        for location in parse_startupjobscz_location(location_text):
            yield {'location': location, 'is_remote': is_remote}
    else:
        yield {'location': None, 'is_remote': is_remote}


def jobs_from_stackoverflowcom(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    elements.make_links_absolute(base_url)

    for job_element in elements.cssselect('.-job-summary'):
        published_ago_element = job_element.cssselect('.-title span')[-1]
        published_ago = normalize_text(published_ago_element.text_content())
        if 'w ago' in published_ago and int(published_ago[0]) > 3:
            continue

        link_element = job_element.cssselect('.-title a')[0]
        url = link_element.get('href')

        company_element = job_element.cssselect('.-company')[0]
        details_elements = list(company_element)

        company_name_element = details_elements[0]
        company_name = normalize_text(company_name_element.text)
        company_url = (f'https://stackoverflow.com/jobs/companies/'
                       + slugify(company_name))

        location_element = details_elements[-1]
        location = normalize_text(location_element.text_content())
        location = LEADING_PUNCTUATION_RE.sub('', location)

        try:
            remote_element = job_element.cssselect('.-remote')[0]
        except IndexError:
            is_remote = False
        else:
            is_remote = 'on-site' not in remote_element.text_content().lower()
        is_relevant = is_remote or is_relevant_location(location)

        yield {
            'url': url,
            'is_remote': is_remote,
            'is_relevant': is_relevant,
            'company_name': company_name,
            'company_url': company_url,
            'location': None if is_remote else location,
        }


def jobs_from_pythonorg(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    elements.make_links_absolute(base_url)

    for heading_element in elements.cssselect('.listing-company'):
        title_element = heading_element.cssselect('.listing-company-name')[0]
        company_name = normalize_text(list(title_element)[-1].tail)

        link_element = heading_element.cssselect('.listing-company-name a')[0]
        url = link_element.get('href')

        location_element = heading_element.cssselect('.listing-location a')[0]
        location = normalize_text(location_element.text_content())
        is_remote = '/telecommute/' in base_url or looks_remote(location)
        is_relevant = is_remote or is_relevant_location(location)

        yield {
            'url': url,
            'is_remote': is_remote,
            'is_relevant': is_relevant,
            'company_name': company_name,
            'company_url': None,
            'location': None if is_remote else location,
        }


def jobs_from_remoteok(response_bytes, base_url):
    for entry in json.loads(response_bytes.decode('utf8')):
        if not entry.get('url') or not entry.get('company'):
            continue

        url = entry['url']
        company_name = entry['company']
        company_url = (f'https://remoteok.io/remote-companies/'
                       + slugify(company_name))

        yield {
            'url': url,
            'is_remote': True,
            'is_relevant': True,
            'company_name': company_name,
            'company_url': company_url,
            'location': None,
        }


def looks_remote(text):
    return REMOTE_RE.search(text.lower()) is not None


def normalize_text(text):
    if text:
        return WHITESPACE_RE.sub(' ', text.strip())
    return text


def embed_location_data(job, location_data):
    return {**job, 'location': {**location_data, 'input': job['location']}}


def is_relevant_location(text):
    return LOCATION_RE.search(text.lower()) is not None


def is_relevant_job(job, agencies):
    if job['company_name'] in agencies:
        return False
    if job['is_relevant']:
        return True
    return False


def parse_geocode_result(geocode_result):
    region = geocode_result.state_long or geocode_result.sublocality
    if region and 'Praha' in region:
        region = 'Praha'
    country = geocode_result.country_long
    return region, country
