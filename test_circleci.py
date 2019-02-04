from pathlib import Path

import pytest
import yaml


BUILDERS_PATH = Path(__file__).parent / 'data'
BUILDERS = [b for b in BUILDERS_PATH.iterdir() if b.is_dir()]


@pytest.fixture
def config():
    path = Path(__file__).parent / '.circleci' / 'config.yml'
    return yaml.safe_load(path.read_text())


@pytest.mark.parametrize('builder', BUILDERS)
def test_ci_config_runs_all_builders(builder, config):
    job_name = f'build_{builder.name}'

    assert job_name in config['jobs']

    job = config['jobs'][job_name]

    assert job['executor'] == 'python'
    assert job['steps'][0] == {'attach_workspace': {'at': '~'}}
    assert job['steps'][1] == {'run': f'pipenv run build {builder.name}'}
    assert job['steps'][2] == {
        'persist_to_workspace': {
            'root': '~',
            'paths': [f'project/data/{builder.name}']
        }
    }


def test_ci_config_fans_out_builders_in_workflow(config):
    default_workflow_jobs = config['workflows']['default_workflow']['jobs']

    builders_job_names = [f'build_{builder.name}' for builder in BUILDERS]
    builders_jobs = [
        {f'build_{builder.name}': {'requires': ['install_and_test']}}
        for builder in BUILDERS
    ]
    builders_count = len(builders_job_names)

    assert default_workflow_jobs[0] == 'install_and_test'
    assert default_workflow_jobs[1:builders_count + 1] == builders_jobs
    assert default_workflow_jobs[builders_count + 1] == {
        'build_web': {'requires': builders_job_names}
    }
