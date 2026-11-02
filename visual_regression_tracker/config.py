import dataclasses
import typing
import os
import os.path
import json
import pathlib

from .exceptions import InvalidConfigurationError, MissingConfigurationError
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
    'httpTimeoutInSeconds': 'VRT_HTTPTIMEOUTINSECONDS',
}


@dataclasses.dataclass
class Config:
    apiUrl: str = 'http://localhost:4200'
    ciBuildId: str = None
    branchName: str = None
    project: str = None
    apiKey: str = None
    enableSoftAssert: bool = False
    httpTimeoutInSeconds: float = 360

    def __setattr__(self, name, value):
        if name == 'apiUrl' and isinstance(value, str):
            value = value.rstrip('/')
        if name == 'httpTimeoutInSeconds' and not _is_seconds(value):
            raise InvalidConfigurationError(
                name, f'{name} ({ENV_MAPPING[name]}) must be a non-negative number of seconds, got {value!r}.')
        super().__setattr__(name, value)

    @staticmethod
    def default(
        path: typing.Union[str, pathlib.Path] = None,
        environment: dict = None,
    ):
        if path:
            cfg = Config.from_file(path)
        elif os.path.isfile(DEFAULT_PATH):
            cfg = Config.from_file(DEFAULT_PATH)
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
            val = environment.get(env_name)
            field_type = fields[field_name]
            if not val:
                continue
            if field_type is str:
                pass
            elif field_type is bool:
                val = val.lower() in ('true', '1')
            elif field_type is float:
                try:
                    val = float(val)
                except ValueError:
                    pass
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


def _is_seconds(value) -> bool:
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0)
