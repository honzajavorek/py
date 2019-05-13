from lxml import html

from pythoncz.pages.jobs.parsing import normalize_text


def jobs_from_bytes(response_bytes, base_url):
    elements = html.fromstring(response_bytes)
    elements.make_links_absolute(base_url)

    for heading_element in elements.cssselect('.listing-company'):
        title_element = heading_element.cssselect('.listing-company-name')[0]
        company_name = normalize_text(list(title_element)[-1].tail)

        link_element = heading_element.cssselect('.listing-company-name a')[0]
        url = link_element.get('href')

        if '/telecommute/' in base_url:
            location_raw = 'remote'
        else:
            location_css = '.listing-location a'
            location_element = heading_element.cssselect(location_css)[0]
            location_raw = normalize_text(location_element.text_content())

        yield {
            'url': url,
            'company_name': company_name,
            'company_url': None,
            'location_raw': location_raw,
        }
