from lxml import html, etree as xml

from pythoncz.pages.jobs.parsing import normalize_text


def jobs_from_bytes(response_bytes, base_url):
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
                'company_name': company_name,
                'company_url': None,
                'location_raw': f'{company_name}, {location}, Česko',
            }


def job_details_from_bytes(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    try:
        location_element = elements.cssselect('a[href*="mapy.cz"]')[0]
    except IndexError:
        yield {}
    else:
        location = normalize_text(location_element.text_content())
        yield {'location': None, 'location_raw': f'{location}, Česko'}
