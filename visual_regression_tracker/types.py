import dataclasses
import enum


@dataclasses.dataclass
class Config:
    apiUrl: str = 'http://localhost:4200'
    branchName: str = None
    project: str = None
    apiKey: str = None


@dataclasses.dataclass
class TestRun:
    name: str = None
    imageBase64: str = None
    os: str = None
    browser: str = None
    viewport: str = None
    device: str = None
    diffTollerancePercent: float = None


@dataclasses.dataclass
class Build:
    id: str = None
    projectId: str = None


class TestRunStatus(enum.Enum):
    NEW = 'new'
    OK = 'ok'
    UNRESOLVED = 'unresolved'


@dataclasses.dataclass
class TestRunResult:
    url: str = None
    status: TestRunStatus = None
    pixelMisMatchCount: float = None
    diffPercent: float = None
    diffTollerancePercent: float = None


def _to_dict(obj):
    fields = dataclasses.fields(obj)
    data = {}
    for field in fields:
        value = getattr(obj, field.name)
        if value is not None:
            data[field.name] = value
    return data


def _from_dict(data, clazz):
    fields = dataclasses.fields(clazz)
    obj = clazz(*[data.get(field.name, None) for field in fields])
    return obj
