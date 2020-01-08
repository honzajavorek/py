from lxml import html
from slugify import slugify

from pythoncz.pages.jobs.parsing import normalize_text


def jobs_from_bytes(response_bytes, base_url):
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

        try:
            remote_element = job_element.cssselect('.-remote')[0]
            is_remote = 'on-site' not in remote_element.text_content().lower()
        except IndexError:
            is_remote = False

        if is_remote:
            location_raw = 'remote'
        else:
            location_element = details_elements[-1]
            location_raw = normalize_text(location_element.text_content())

        yield {
            'url': url,
            'company_name': company_name,
            'company_url': company_url,
            'location_raw': location_raw,
        }
