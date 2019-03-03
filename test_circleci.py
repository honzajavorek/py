from pathlib import Path

import pytest
import yaml


PROJECT_PATH = Path(__file__).parent

PAGES_PATH = PROJECT_PATH / 'pythoncz' / 'pages'
PAGE_BUILDERS_NAMES = [
    item.name for item in PAGES_PATH.iterdir()
    if item.is_dir() and (PAGES_PATH / item / '__main__.py').is_file()
]


@pytest.fixture
def config():
    path = Path(__file__).parent / '.circleci' / 'config.yml'
    return yaml.safe_load(path.read_text())


@pytest.mark.parametrize('builder_name', PAGE_BUILDERS_NAMES)
def test_ci_config_runs_all_page_builders(builder_name, config):
    job_name = f'build_{builder_name}'

    assert job_name in config['jobs']

    job = config['jobs'][job_name]

    assert job['executor'] == 'python'
    assert job['steps'][0] == {'attach_workspace': {'at': '~'}}
    assert job['steps'][1] == {'run': f'pipenv run build {builder_name}'}
    assert job['steps'][2] == {
        'persist_to_workspace': {
            'root': '~',
            'paths': [f'project/pythoncz/pages/{builder_name}/*_data.json']
        }
    }


def test_ci_config_fans_out_page_builders_in_workflow(config):
    default_workflow_jobs = config['workflows']['default_workflow']['jobs']

    builders_job_names = [
        f'build_{builder_name}'
        for builder_name in PAGE_BUILDERS_NAMES
    ]
    builders_jobs = [
        {f'build_{builder_name}': {'requires': ['install_and_test']}}
        for builder_name in PAGE_BUILDERS_NAMES
    ]
    builders_count = len(builders_job_names)

    assert default_workflow_jobs[0] == 'install_and_test'
    assert default_workflow_jobs[1:builders_count + 1] == builders_jobs
    assert default_workflow_jobs[builders_count + 1] == {
        'build_web': {'requires': builders_job_names}
    }
