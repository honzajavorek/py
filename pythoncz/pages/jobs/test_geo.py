import pytest

from pythoncz.pages.jobs import geo


@pytest.mark.parametrize('location_raw,location', [
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
def test_parse_countries(location_raw, location):
    assert geo.parse(location_raw) == location


@pytest.mark.parametrize('location_raw,location', [
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
def test_parse_regional_centers(location_raw, location):
    assert geo.parse(location_raw) == location


@pytest.mark.parametrize('location_raw,location', [
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
def test_parse_regions(location_raw, location):
    assert geo.parse(location_raw) == location


@pytest.mark.parametrize('location_raw', [
    'Česká republika',
    'Czech Republic',
    'Česko',
    'Czechia',
    'Praha, externě',
    'Remote, Worldwide',
    '100% Remote, You decide where you work',
    'Anywhere, Anywhere',
])
def test_parse_remote(location_raw):
    assert geo.parse(location_raw) == 'remote'


@pytest.mark.parametrize('location_raw', [
    'On-site and limited remote',
    'New York, NY 10016, USA',
    'London, United Kingdom',
])
def test_parse_out_of_scope(location_raw):
    assert geo.parse(location_raw) == 'out_of_scope'


@pytest.mark.parametrize('location_raw', [
    'Nový dvůr 232, Letohrad, Česká republika',
    'Česká Třebová',
    'Bruntál, Česko',
])
def test_parse_no_match(location_raw):
    assert geo.parse(location_raw) is None


def test_resolve_location_can_be_parsed():
    def geocode(location_raw):
        raise AssertionError('This scenario should not call geocode()')

    location_raw = 'Uliční 1, Brno, Česká republika'
    location = geo.resolve(location_raw, geocode=geocode)

    assert location == 'cz_jhm'


def test_resolve_location_geocoded():
    def geocode(location_raw):
        return 'Pardubický kraj, Česko'

    location_raw = 'Nový dvůr 232, Letohrad, Česká republika'
    location = geo.resolve(location_raw, geocode=geocode)

    assert location == 'cz_pak'


def test_resolve_location_geocoded_but_out_of_scope():
    def geocode(location_raw):
        return 'Washington, USA'

    location_raw = 'Embassy of Czechia, USA'
    location = geo.resolve(location_raw, geocode=geocode)

    assert location == 'out_of_scope'
