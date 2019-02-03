import re
import os
import json
import shlex
import subprocess
from pathlib import Path

import click
from slugify import slugify


PROJECT_PATH = Path(__file__).parent.parent
BUILDERS_PATH = PROJECT_PATH / 'data'
WEB_BUILD_PATH = PROJECT_PATH / 'web' / 'build'

BUILDERS_NAMES = [b.name for b in BUILDERS_PATH.iterdir() if b.is_dir()]


@click.group()
def cli():
    pass


@cli.command()
@click.argument('target', required=False)
def build(target=None):
    if target in BUILDERS_NAMES:
        log(f'Building data for {target}')
        run(f'python -m data.{target}')

    elif target == 'web':
        log(f'Building the website into {WEB_BUILD_PATH}')
        run(f'python -m web freeze --path={WEB_BUILD_PATH} --no-cname')

    else:
        for builder in BUILDERS_NAMES:
            log(f'Building data for {builder}')
            run(f'python -m data.{builder}')
        log(f'Building the website into {WEB_BUILD_PATH}')
        run(f'python -m web freeze --path={WEB_BUILD_PATH} --no-cname')


@cli.command()
@click.argument('name', required=False)
def deploy(name=None):
    deployment_name = to_deployment_name(name)

    now_config = create_now_config(deployment_name, [
        path.relative_to(WEB_BUILD_PATH)
        for path in WEB_BUILD_PATH.glob('**/*')
    ])
    now_config_path = WEB_BUILD_PATH / 'now.json'
    log(f'Writing {now_config_path}')
    now_config_path.write_text(json.dumps(now_config))

    token = os.getenv('NOW_TOKEN') or None
    token_option = f'--token={token}' if token else ''

    log(f'Deploying {WEB_BUILD_PATH}')
    run(f'now {WEB_BUILD_PATH} {token_option}')

    alias_url = f'{deployment_name}.now.sh'
    deployments_list = run(f'now ls {deployment_name} {token_option}',
                           stdout=True).stdout.decode('utf-8')
    deployment_url = re.search(deployment_name + r'-[^\.]+\.now\.sh',
                               deployments_list).group(0)
    log(f'Aliasing {deployment_url} to {alias_url}')
    run(f'now alias {deployment_url} {alias_url} {token_option}')


def to_deployment_name(name):
    if name == 'master' or name is None:
        return 'pythoncz'
    return f'pythoncz-{slugify(name)}'


def create_now_config(deployment_name, paths):
    return {
        'version': 2,
        'name': deployment_name,
        'builds': [path_to_now_build(path) for path in paths],
    }


def path_to_now_build(path):
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
