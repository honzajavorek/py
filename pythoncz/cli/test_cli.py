from pathlib import Path

import pytest

from pythoncz import cli


@pytest.mark.parametrize('name,expected', [
    (None, 'pythoncz'),
    ('master', 'pythoncz'),
    ('branch-name', 'pythoncz-branch-name'),
    ('pyvec/branch-name', 'pythoncz-pyvec-branch-name'),
])
def test_to_deployment_name(name, expected):
    assert cli.to_deployment_name(name) == expected


def test_create_now_config():
    deployment_name = 'pythoncz-pyvec-branch-name'
    paths = [
        Path('index.html'),
        Path('pages/index.html'),
        Path('images/avatar.png'),
        Path('robots.txt'),
    ]

    assert cli.create_now_config(deployment_name, paths) == {
        'version': 2,
        'name': 'pythoncz-pyvec-branch-name',
        'builds': [
            {'src': 'index.html', 'use': '@now/html-minifier'},
            {'src': 'pages/index.html', 'use': '@now/html-minifier'},
            {'src': 'images/avatar.png', 'use': '@now/optipng'},
            {'src': 'robots.txt', 'use': '@now/static'},
        ]
    }


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
