import json
import sys
import types

import pytest

from visual_regression_tracker import Config, MissingConfigurationError
from visual_regression_tracker.config import ENV_MAPPING


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
        'httpTimeoutInSeconds': 5,
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
        'VRT_ENABLESOFTASSERT': 'False',
        'VRT_HTTPTIMEOUTINSECONDS': '7.5',
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
    assert cfg.httpTimeoutInSeconds == 5


def test_config_from_environment(config_env):
    cfg = Config.from_environment(config_env)
    assert cfg.apiUrl == 'env api url'
    assert cfg.ciBuildId == 'env ci build id'
    assert cfg.branchName == 'env branch name'
    assert cfg.project == 'env project'
    assert cfg.apiKey == 'env api key'
    assert cfg.enableSoftAssert == False
    assert cfg.httpTimeoutInSeconds == 7.5


def test_config_timeout_defaults_to_30_seconds():
    assert Config().httpTimeoutInSeconds == 30


@pytest.mark.parametrize('make_config', [
    lambda: Config(apiUrl='http://vrt:4200/'),
    lambda: Config.from_environment({'VRT_APIURL': 'http://vrt:4200/'}),
])
def test_config_strips_trailing_slash_from_apiUrl(make_config):
    assert make_config().apiUrl == 'http://vrt:4200'


def test_config_from_file_strips_trailing_slash_from_apiUrl(tmp_path):
    path = tmp_path / 'vrt.json'
    path.write_text(json.dumps({'apiUrl': 'http://vrt:4200/'}))
    assert Config.from_file(path).apiUrl == 'http://vrt:4200'


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
    del config_env['VRT_HTTPTIMEOUTINSECONDS']

    cfg = Config.default(environment=config_env)
    assert cfg.apiUrl == Config.apiUrl
    assert cfg.ciBuildId is None
    assert cfg.httpTimeoutInSeconds == 30


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


def test_default_reads_vrt_json_from_working_directory_when_run_by_a_script(tmp_path, monkeypatch):
    (tmp_path / 'vrt.json').write_text(json.dumps({
        'apiUrl': 'http://vrt:4200',
        'branchName': 'develop',
        'project': 'project',
        'apiKey': 'key',
    }))
    script = types.ModuleType('__main__')
    script.__file__ = '/venv/bin/pytest'
    script.__spec__ = None
    monkeypatch.setitem(sys.modules, '__main__', script)
    monkeypatch.chdir(tmp_path)

    cfg = Config.default(environment={})

    assert cfg.project == 'project'
