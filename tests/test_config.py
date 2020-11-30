import json
import os
import pytest
import pathlib
import subprocess
import sys

from visual_regression_tracker import Config, MissingConfigurationError
from visual_regression_tracker.config import \
    determine_config_path, REQUIRED_PROPERTIES, ENV_MAPPING


@pytest.fixture
def config_file(tmpdir):
    p = tmpdir.join('config.json')
    p.write(json.dumps({
        'apiUrl': 'file api url',
        'ciBuildId': 'file ci build id',
        'branchName': 'file branch name',
        'project': 'file project',
        'apiKey': 'file api key',
        'enableSoftAssert': True,
    }))
    yield p


@pytest.fixture
def config_env():
    env = {
        'VRT_APIURL': 'env api url',
        'VRT_CIBUILDID': 'env ci build id',
        'VRT_BRANCHNAME': 'env branch name',
        'VRT_PROJECT': 'env project',
        'VRT_APIKEY': 'env api key',
        'VRT_ENABLESOFTASSERT': False,
    }
    yield env


def test_config_from_file(config_file):
    cfg = Config.from_file(config_file)
    assert cfg.apiUrl == 'file api url'
    assert cfg.ciBuildId == 'file ci build id'
    assert cfg.branchName == 'file branch name'
    assert cfg.project == 'file project'
    assert cfg.apiKey == 'file api key'
    assert cfg.enableSoftAssert == True


def test_config_from_environment(config_env):
    cfg = Config.from_environment(config_env)
    assert cfg.apiUrl == 'env api url'
    assert cfg.ciBuildId == 'env ci build id'
    assert cfg.branchName == 'env branch name'
    assert cfg.project == 'env project'
    assert cfg.apiKey == 'env api key'
    assert cfg.enableSoftAssert == False


def test_default_uses_path(config_file):
    cfg = Config.default(path=config_file, environment={})
    assert cfg.apiUrl == 'file api url'
    assert cfg.ciBuildId == 'file ci build id'
    assert cfg.branchName == 'file branch name'
    assert cfg.project == 'file project'
    assert cfg.apiKey == 'file api key'
    assert cfg.enableSoftAssert == True


def test_default_uses_default_path(mocker, config_file):
    config_file_data = open(config_file).read()
    mocker.patch('builtins.open', mocker.mock_open(read_data=config_file_data))
    mocker.patch('os.path.isfile').return_value = True

    cfg = Config.default(environment={})
    assert cfg.apiUrl == 'file api url'
    assert cfg.ciBuildId == 'file ci build id'
    assert cfg.branchName == 'file branch name'
    assert cfg.project == 'file project'
    assert cfg.apiKey == 'file api key'
    assert cfg.enableSoftAssert == True


def test_default_uses_environment(config_env, mocker):
    mocker.patch('os.path.isfile').return_value = False

    cfg = Config.default(environment=config_env)
    assert cfg.apiUrl == 'env api url'
    assert cfg.ciBuildId == 'env ci build id'
    assert cfg.branchName == 'env branch name'
    assert cfg.project == 'env project'
    assert cfg.apiKey == 'env api key'
    assert cfg.enableSoftAssert == False


def test_default_uses_defaults(config_env, mocker):
    mocker.patch('os.path.isfile').return_value = False
    del config_env['VRT_CIBUILDID']
    del config_env['VRT_APIURL']

    cfg = Config.default(environment=config_env)
    assert cfg.apiUrl == Config.apiUrl
    assert cfg.ciBuildId is None


def test_default_prefers_environment(config_env, config_file):
    del config_env['VRT_PROJECT']
    cfg = Config.default(path=config_file, environment=config_env)
    assert cfg.ciBuildId == 'env ci build id'
    assert cfg.project == 'file project'


def test_default_raises_on_invalid_path():
    with pytest.raises(IOError):
        Config.default(path='/does/not/exist/vrt.json')


@pytest.mark.parametrize('missing_field', ['branchName', 'project', 'apiKey'])
def test_default_raises_on_missing_settings(mocker, config_env, missing_field):
    mocker.patch('os.path.isfile').return_value = False
    del config_env[ENV_MAPPING[missing_field]]

    with pytest.raises(MissingConfigurationError):
        Config.default(environment=config_env)


def test_determine_config_path_from_pytest():
    current_file = pathlib.Path(__file__)
    sdk_python_dir = str(current_file.parent.parent)
    assert determine_config_path() == sdk_python_dir


@pytest.fixture
def change_current_dir(tmpdir):
    olddir = os.curdir
    os.chdir(os.path.expanduser('~'))
    yield os.path.abspath(os.curdir)
    os.chdir(olddir)


def test_detemine_config_path_from_repl(change_current_dir):
    current_file = pathlib.Path(__file__)
    sdk_python_dir = str(current_file.parent.parent)

    output = subprocess.check_output(
        sys.executable,
        encoding='ascii',
        input=f'''
import sys
sys.path.insert(0, '{sdk_python_dir}')

from visual_regression_tracker.config import determine_config_path
print(determine_config_path())
quit()
'''
    )
    result = output.strip()
    assert result == change_current_dir

