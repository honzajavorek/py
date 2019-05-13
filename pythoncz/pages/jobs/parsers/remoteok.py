import json

from slugify import slugify


def jobs_from_bytes(response_bytes, base_url):
    for entry in json.loads(response_bytes.decode('utf8')):
        if not entry.get('url') or not entry.get('company'):
            continue

        url = entry['url']
        company_name = entry['company']
        company_url = (f'https://remoteok.io/remote-companies/'
                       + slugify(company_name))

        yield {
            'url': url,
            'company_name': company_name,
            'company_url': company_url,
            'location_raw': 'remote',
        }
