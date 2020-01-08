from lxml import html, etree as xml

from pythoncz.pages.jobs import geo
from pythoncz.pages.jobs.parsing import normalize_text


def jobs_from_bytes(response_bytes, base_url):
    elements = xml.fromstring(response_bytes)
    for job_element in elements.iterfind('.//offer'):
        url = normalize_text(job_element.find('url').text)

        company_element = job_element.find('startup')
        company_name = normalize_text(company_element.text)

        company_url_element = job_element.find('startupURL')
        company_url = normalize_text(company_url_element.text)

        yield {
            'url': url,
            'company_name': company_name,
            'company_url': company_url,
            'location_raw': 'Česko',
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


def job_details_from_bytes(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    elements.make_links_absolute(base_url)

    job_details_element = elements.cssselect('#offer-detail .details')[0]
    location_element, _, job_type_element = list(job_details_element)

    if geo.parse(job_type_element.text_content()) == 'remote':
        yield {'location': None, 'location_raw': 'remote'}
    else:
        location_text = normalize_text(location_element.text_content())
        for location_raw in parse_startupjobscz_location(location_text):
            yield {'location': None, 'location_raw': location_raw}
