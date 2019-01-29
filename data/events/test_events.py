from . import build


def test_builder():
    assert build({}) == [{'name': 'Pyvo'}]
