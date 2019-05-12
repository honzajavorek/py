import pytest

from pythoncz.pages.jobs import geo


@pytest.mark.parametrize('raw_location,location', [
    ('Slovenská republika', 'sk'),
    ('Slovak Republic', 'sk'),
    ('Slovensko', 'sk'),
    ('Bratislava, Slovakia', 'sk'),
    ('Berlin, Deutschland', 'de'),
    ('Německo', 'de'),
    ('Frankfurt/Main, Hassia, Germany', 'de'),
    ('Polska', 'pl'),
    ('Polsko', 'pl'),
    ('Kraków, Poland', 'pl'),
    ('Linz, Österreich', 'at'),
    ('Ȍsterreich', 'at'),
    ('Osterreich', 'at'),
    ('Rakousko', 'at'),
    ('Vienna, Austria', 'at'),
])
def test_parse_countries(raw_location, location):
    assert geo.parse(raw_location) == location


@pytest.mark.parametrize('raw_location,location', [
    ('Uliční 1, Praha, Česko', 'cz_pha'),
    ('Uliční 1, Prague, Česko', 'cz_pha'),
    ('Uliční 1, Praha 3, Česko', 'cz_pha'),
    ('Uliční 1, Praha 3-Žižkov, Česko', 'cz_pha'),
    ('Uliční 1, Kladno, Česko', 'cz_stc'),
    ('Uliční 1, Č. Budějovice, Česko', 'cz_jhc'),
    ('Uliční 1, Pilsen, Česko', 'cz_plk'),
    ('Uliční 1, K. Vary, Česko', 'cz_kvk'),
    ('Uliční 1, Ústí n.Labem, Česko', 'cz_ulk'),
    ('Uliční 1, Liberec, Česko', 'cz_lbk'),
    ('Uliční 1, H. Králové, Česko', 'cz_hkk'),
    ('Uliční 1, Pardubice, Česko', 'cz_pak'),
    ('Uliční 1, Olomouc, Česko', 'cz_olk'),
    ('Uliční 1, Ostrava, Česko', 'cz_msk'),
    ('Uliční 1, Brno, Česko', 'cz_jhm'),
    ('Uliční 1, Zlín, Česko', 'cz_zlk'),
    ('Uliční 1, Jihlava, Česko', 'cz_vys'),
])
def test_parse_regional_centers(raw_location, location):
    assert geo.parse(raw_location) == location


@pytest.mark.parametrize('raw_location,location', [
    ('Uliční 1, Hlavní město Praha', 'cz_pha'),
    ('Uliční 1, Město, Středočeský kraj', 'cz_stc'),
    ('Uliční 1, Město, Jihočeský kraj', 'cz_jhc'),
    ('Uliční 1, Město, Plzeňský kraj', 'cz_plk'),
    ('Uliční 1, Město, Karlovarský kraj', 'cz_kvk'),
    ('Uliční 1, Město, Ústecký kraj', 'cz_ulk'),
    ('Uliční 1, Město, Liberecký kraj', 'cz_lbk'),
    ('Uliční 1, Město, Královéhradecký kraj', 'cz_hkk'),
    ('Uliční 1, Město, Pardubický kraj', 'cz_pak'),
    ('Uliční 1, Město, Olomoucký kraj', 'cz_olk'),
    ('Uliční 1, Město, Moravskoslezský kraj', 'cz_msk'),
    ('Uliční 1, Město, Jihomoravský kraj', 'cz_jhm'),
    ('Uliční 1, Město, Zlínský kraj', 'cz_zlk'),
    ('Uliční 1, Město, Kraj Vysočina', 'cz_vys'),
])
def test_parse_regions(raw_location, location):
    assert geo.parse(raw_location) == location


@pytest.mark.parametrize('raw_location', [
    'Česká republika',
    'Czech Republic',
    'Česko',
    'Czechia',
    'Praha, externě',
    'Remote, Worldwide',
    '100% Remote, You decide where you work',
    'Anywhere, Anywhere',
])
def test_parse_remote(raw_location):
    assert geo.parse(raw_location) == 'remote'


@pytest.mark.parametrize('raw_location', [
    'On-site and limited remote',
    'New York, NY 10016, USA',
    'London, United Kingdom',
])
def test_parse_out_of_scope(raw_location):
    assert geo.parse(raw_location) == 'out_of_scope'


@pytest.mark.parametrize('raw_location', [
    'Nový dvůr 232, Letohrad, Česká republika',
    'Česká Třebová',
    'Bruntál, Česko',
])
def test_parse_no_match(raw_location):
    assert geo.parse(raw_location) is None


def test_query_location_can_be_parsed():
    query = geo.query('Uliční 1, Brno, Česká republika')
    with pytest.raises(StopIteration) as excinfo:
        next(query)

    assert excinfo.value.value == 'cz_jhm'


def test_execute_location_can_be_parsed():
    def geocode():
        raise AssertionError('This scenario should not call geocode()')

    query = geo.query('Uliční 1, Brno, Česká republika')
    location = geo.execute(query, geocode=geocode)

    assert location == 'cz_jhm'


def test_query_location_geocoded():
    query = geo.query('Nový dvůr 232, Letohrad, Česká republika')
    raw_location = next(query)

    with pytest.raises(StopIteration) as excinfo:
        query.send('Pardubický kraj, Česko')

    assert raw_location == 'Nový dvůr 232, Letohrad, Česká republika'
    assert excinfo.value.value == 'cz_pak'


def test_execute_location_geocoded():
    query = geo.query('Nový dvůr 232, Letohrad, Česká republika')
    location = geo.execute(query, geocode=lambda _: 'Pardubický kraj, Česko')

    assert location == 'cz_pak'


def test_query_location_geocoded_but_out_of_scope():
    query = geo.query('Embassy of Czechia, USA')
    raw_location = next(query)

    with pytest.raises(StopIteration) as excinfo:
        query.send('Washington, USA')

    assert raw_location == 'Embassy of Czechia, USA'
    assert excinfo.value.value == 'out_of_scope'


def test_execute_location_geocoded_but_out_of_scope():
    query = geo.query('Embassy of Czechia, USA')
    location = geo.execute(query, geocode=lambda _: 'Washington, USA')

    assert location == 'out_of_scope'


def test_execute_unexpected_query_behavior():
    def create_query():
        while True:
            yield 'New York, NY 10016, USA'

    with pytest.raises(RuntimeError):
        geo.execute(create_query(), geocode=lambda _: 'New York, USA')
