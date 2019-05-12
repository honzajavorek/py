import re
import json
from pathlib import Path
from datetime import datetime

from arrow import Arrow

from pythoncz import log


logger = log.get(__name__)


DATETIME_RE = re.compile(r'''
^
    \d{4}-\d{2}-\d{2}   # date
    T                   # separator
    \d{2}:\d{2}:\d{2}   # time
    [+\-]\d{2}:\d{2}    # timezone
$
''', re.VERBOSE)


def save_data(data_path, data):
    data_path = Path(data_path)
    data_json = json.dumps(data, ensure_ascii=False, indent=2,
                           default=encode_datetime)
    data_path.write_text(data_json)


def encode_datetime(o):
    if isinstance(o, (Arrow, datetime)):
        return o.isoformat()
    raise TypeError(f'Object of type {o.__class__.__name__} '
                    + 'is not JSON serializable')


def load_data(data_path, default=None, debug=False):
    data_path = Path(data_path)
    assert data_path.match('*_data.json')

    package_path = data_path.parent
    assert package_path.parts[-3] == 'pythoncz'
    assert package_path.parts[-2] == 'pages'

    try:
        data_json = data_path.read_text()
    except FileNotFoundError:
        if debug:
            build_command = f'pipenv run build {package_path.parts[-1]}'
            message = (
                "There is no data in '%s'. Run '%s' "
                "and retry the request to see content"
            )
            logger.warning(message, data_path, build_command)
            return default
        else:
            raise
    else:
        return json.loads(data_json, object_hook=decode_datetime)


def decode_datetime(o):
    for key, value in o.items():
        if isinstance(value, str) and DATETIME_RE.match(value):
            o[key] = datetime.fromisoformat(value)
    return o
