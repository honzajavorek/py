import re
import functools

import geocoder
from unidecode import unidecode


def patterns(*patterns):
    return [re.compile(pattern, re.I) for pattern in patterns]


CZECH_PATTERNS = patterns(r'\bčesk', r'\bczech')
PARSE_PATTERNS = (
    ('remote', patterns(r'(?<!limited )\bremote\b', r'\banywhere\b',
                        r'\bexterně\b', r'^česk(o|á republika)$',
                        r'^czech(ia| republic)?$')),

    # using ISO 3166-1 alpha-2 contry codes
    ('sk', patterns(r'\bslovensk', r'\bslovak')),
    ('de', patterns(r'\bdeutschland\b', r'\bgermany\b', r'\bněmecko\b')),
    ('pl', patterns(r'\bpolsko\b', r'\bpolska\b', r'\bpoland\b')),
    ('at', patterns(r'\b[oȍö]sterreich', r'\brakousko\b', r'\baustria\b')),

    # regions, their centers, and top 20 largest Czech cities by inhabitants
    # (using ČSÚ region codes)
    ('cz_pha', patterns(r'\bpraha\b', r'\bprague\b')),
    ('cz_stc', patterns(r'\bkladno\b', r'\bstředočeský\b')),
    ('cz_jhc', patterns(r'\bč(eské|\.) budějovice\b', r'\bjihočeský\b',
                        r'\bbudějovický\b')),
    ('cz_plk', patterns(r'\bplzeň\b', r'\bpilsen\b', r'\bplzeňský\b',
                        r'\bzápadočeský\b')),
    ('cz_kvk', patterns(r'\bk(arlovy|\.) vary\b', r'\bkarlovarský\b')),
    ('cz_ulk', patterns(r'\bústí (nad |n |n\.)(labem|l\.)\b', r'\bmost\b',
                        r'\bděčín\b', r'\bteplice\b', r'\bústecký\b',
                        r'\bseveročeský\b')),
    ('cz_lbk', patterns(r'\bliberec\b', r'\bliberecký\b')),
    ('cz_hkk', patterns(r'\bh(radec|\.) králové\b', r'\bvýchodočeský\b',
                        r'\bhradec k(rálové|\.)\b', r'\bkrálovéhradecký\b')),
    ('cz_pak', patterns(r'\bpardubice\b', r'\bpardubický\b')),
    ('cz_olk', patterns(r'\bolomouc\b', r'\bolomoucký\b')),
    ('cz_msk', patterns(r'\bostrava\b', r'\bopava\b', r'\bkarviná\b',
                        r'\bfrýdek\s*-\s*místek\b', r'\bhavířov\b',
                        r'\bmoravskoslezský\b', r'\bseveromoravský\b',
                        r'\bostravský\b')),
    ('cz_jhm', patterns(r'\bbrno\b', r'\bjihomoravský\b', r'\bbrněnský\b')),
    ('cz_zlk', patterns(r'\bzlín\b', r'\bzlínský\b')),
    ('cz_vys', patterns(r'\bjihlava\b', r'\bvysočina\b')),
)


def parse(raw_location):
    for location_code, patterns in PARSE_PATTERNS:
        for pattern in patterns:
            if pattern.search(raw_location):
                return location_code

    if not any([pattern.search(raw_location) for pattern in CZECH_PATTERNS]):
        return 'out_of_scope'
    return None  # is within scope, but could not be parsed


@functools.lru_cache()
def geocode(raw_location, **options):
    api_key = options.get('api_key')

    result = geocoder.google(unidecode(raw_location), key=api_key,
                             language='cs', region='cz')
    region = result.state_long or result.locality
    country = result.country_long

    if ',' in raw_location and not region:
        result = geocoder.google(result.latlng, key=api_key, method='reverse',
                                 language='cs', region='cz')
        region = result.state_long or result.locality
        country = result.country_long

    return ', '.join(filter(None, [region, country]))


# To make following part testable, it is heavily inspired by the interface
# of https://github.com/ariebovenberg/snug/


def query(raw_location):
    location_code = parse(raw_location)
    if location_code is None:
        location = yield raw_location
        return parse(location)
    return location_code


def execute(query, **options):
    try:
        raw_location = next(query)
    except StopIteration as e:
        return e.value
    else:
        geocode_fn = options.pop('geocode', geocode)
        location = geocode_fn(raw_location, **options)
        try:
            query.send(location)
        except StopIteration as e:
            return e.value or 'out_of_scope'
        else:
            raise RuntimeError('Location query did not return any value')
