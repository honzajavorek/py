import os
import json
import shlex
import urllib
import warnings
import subprocess
from pathlib import Path

import click
import flask_frozen

from pythoncz import app, log


logger = log.get(__name__)


PROJECT_PATH = Path(__file__).parent.parent.parent
NOW_CONFIG_DEFAULTS = PROJECT_PATH / 'now-defaults.json'

PAGES_PATH = PROJECT_PATH / 'pythoncz' / 'pages'
PAGE_BUILDERS_NAMES = [
    item.name for item in PAGES_PATH.iterdir()
    if item.is_dir() and (PAGES_PATH / item / '__main__.py').is_file()
]

WEB_BUILD_PATH = PROJECT_PATH / 'build'
WEB_BASE_URL = 'https://python.cz'


@click.group()
def cli():
    pass


@cli.command()
@click.option('--port', type=int, default=8000, help='Port to listen at')
def serve(port):
    app.run(host='0.0.0.0', port=port, debug=True)


@cli.command()
@click.argument('target', required=False)
@click.pass_context
def build(ctx, target=None):
    if target in PAGE_BUILDERS_NAMES:
        build_page(target)
    elif target == 'web':
        build_web(app, WEB_BASE_URL, WEB_BUILD_PATH)
    else:
        for page_name in PAGE_BUILDERS_NAMES:
            build_page(page_name)
        build_web(app, WEB_BASE_URL, WEB_BUILD_PATH)


def build_page(name):
    log(f'Building data for {name}')
    run(f'python -m pythoncz.pages.{name}')


def build_web(app, base_url, build_path):
    log(f'Building web into {build_path}')
    warnings.filterwarnings('error', category=flask_frozen.FrozenFlaskWarning)

    app.config['FREEZER_DESTINATION'] = build_path
    app.config['FREEZER_BASE_URL'] = base_url
    app.config['SERVER_NAME'] = urllib.parse.urlparse(base_url).netloc

    freezer = flask_frozen.Freezer(app)
    for page in freezer.freeze_yield():
        logger.info(f'Web path {page.url} done')


@cli.command()
@click.argument('target', required=False)
def deploy(target=None):
    now_config = json.loads(NOW_CONFIG_DEFAULTS.read_text())
    now_config['builds'] = to_now_builds([
        path.relative_to(WEB_BUILD_PATH)
        for path in WEB_BUILD_PATH.glob('**/*')
    ])

    now_config_path = WEB_BUILD_PATH / 'now.json'
    log(f'Writing {now_config_path}')
    now_config_path.write_text(json.dumps(now_config))

    token = os.getenv('NOW_TOKEN') or None
    token_option = f'--token={token}' if token else ''

    target = target or os.getenv('NOW_TARGET') or None
    target_option = f'--target={target}' if target else ''

    log(f'Deploying {WEB_BUILD_PATH} to {target}')
    run(f'now {WEB_BUILD_PATH} {target_option} {token_option}')


def to_now_builds(paths):
    # Beware! This function is taking care of 'now.sh builds', which are
    # something completely different than 'page builders' mentioned elsewhere
    # in the python.cz project.
    return [path_to_now_build(path) for path in paths]


def path_to_now_build(path):
    # Beware! This function is taking care of 'now.sh builds', which are
    # something completely different than 'page builders' mentioned elsewhere
    # in the python.cz project.
    if path.match('*.html'):
        return {'src': str(path), 'use': '@now/html-minifier'}
    if path.match('*.png'):
        return {'src': str(path), 'use': '@now/optipng'}
    return {'src': str(path), 'use': '@now/static'}


def run(command, stdout=False):
    stdout = subprocess.PIPE if stdout else None
    return subprocess.run(shlex.split(command), stdout=stdout,
                          check=True, cwd=PROJECT_PATH)


def log(message):
    click.secho(message, bold=True, fg='blue')
