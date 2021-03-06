from pathlib import Path

import pytest

from pythoncz import cli


def test_to_now_builds():
    assert cli.to_now_builds([
        Path('index.html'),
        Path('pages/index.html'),
        Path('images/avatar.png'),
        Path('robots.txt'),
    ]) == [
        {'src': 'index.html', 'use': '@now/html-minifier'},
        {'src': 'pages/index.html', 'use': '@now/html-minifier'},
        {'src': 'images/avatar.png', 'use': '@now/optipng'},
        {'src': 'robots.txt', 'use': '@now/static'},
    ]


@pytest.mark.parametrize('path,expected_src,expected_use', [
    (Path('index.html'), 'index.html', '@now/html-minifier'),
    (Path('foo/bar/index.html'), 'foo/bar/index.html', '@now/html-minifier'),
    (Path('image.png'), 'image.png', '@now/optipng'),
    (Path('image.jpg'), 'image.jpg', '@now/static'),
    (Path('robots.txt'), 'robots.txt', '@now/static'),
])
def test_path_to_now_build(path, expected_src, expected_use):
    assert cli.path_to_now_build(path) == {
        'src': expected_src,
        'use': expected_use,
    }
