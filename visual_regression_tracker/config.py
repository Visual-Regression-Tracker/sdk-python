import dataclasses
import typing
import os
import os.path
import json
import pathlib
import sys

from .exceptions import MissingConfigurationError
from .types import _from_dict


DEFAULT_PATH = 'vrt.json'
REQUIRED_PROPERTIES = ['apiUrl', 'branchName', 'project', 'apiKey']
ENV_MAPPING = {
    'apiUrl': 'VRT_APIURL',
    'ciBuildId': 'VRT_CIBUILDID',
    'branchName': 'VRT_BRANCHNAME',
    'project': 'VRT_PROJECT',
    'apiKey': 'VRT_APIKEY',
    'enableSoftAssert': 'VRT_ENABLESOFTASSERT',
}


@dataclasses.dataclass
class Config:
    apiUrl: str = 'http://localhost:4200'
    ciBuildId: str = None
    branchName: str = None
    project: str = None
    apiKey: str = None
    enableSoftAssert: bool = False

    @staticmethod
    def default(
        path: typing.Union[str, pathlib.Path] = None,
        environment: dict = None,
    ):
        default_path = os.path.join(determine_config_path(), DEFAULT_PATH)

        if path:
            cfg = Config.from_file(path)
        elif os.path.isfile(default_path):
            cfg = Config.from_file(default_path)
        else:
            cfg = Config()

        cfg.apply_environment(environment or os.environ)

        try:
            cfg.check_complete()
        except MissingConfigurationError as e:
            raise MissingConfigurationError(
                e.field,
                f'Incomplete configuration, {e.field} was not specified.',
                'Please provide via the constructor, a config file "vrt.json", or environment variables.'
            )

        return cfg

    @staticmethod
    def from_file(path: typing.Union[str, pathlib.Path]):
        with open(path, 'r') as f:
            cfg = _from_dict(json.load(f), Config)
        return cfg

    def apply_environment(self, environment: dict = None):
        fields = {f.name:f.type for f in dataclasses.fields(self)}
        for field_name, env_name in ENV_MAPPING.items():
            val = environment.get(env_name, None)
            field_type = fields[field_name]
            if val is None:
                continue
            if field_type is str:
                pass
            elif field_type is bool:
                val = val.lower() in ('true', '1')
            else:
                raise Exception('Unsupported type')
            setattr(self, field_name, val)

    @staticmethod
    def from_environment(environment: dict = None):
        cfg = Config()
        cfg.apply_environment(environment)
        return cfg

    def check_complete(self):
        for field_name in REQUIRED_PROPERTIES:
            if getattr(self, field_name) is None:
                raise MissingConfigurationError(field_name, f'{field_name} is not specified.')


def determine_config_path():
    """
    Determines the absolute path to the directory the current project is in:
    1. If in a script, then use the directory the script is in.
    2. If in a REPL, then use PWD.
    3. If running an installed module (ours or 3rd-party), then use PWD.
    """
    main_module = sys.modules['__main__'].__dict__
    is_script = '__file__' in main_module and main_module['__spec__'] is None
    rel_dir = os.path.dirname(main_module['__file__']) if is_script else os.curdir
    abs_dir = os.path.abspath(rel_dir)
    return abs_dir
