import dataclasses
import enum


@dataclasses.dataclass
class Config:
    apiUrl: str = 'http://localhost:4200'
    branchName: str = None
    project: str = None
    apiKey: str = None
    enableSoftAssert: bool = False


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
class TestRunResponse:
    id: str = None
    imageName: str = None
    diffName: str = None
    baselineName: str = None
    url: str = None
    merge: bool = False
    status: TestRunStatus = None
    pixelMisMatchCount: float = None
    diffPercent: float = None
    diffTollerancePercent: float = None


@dataclasses.dataclass
class TestRunResult:
    testRunResponse: TestRunResponse = None
    imageUrl: str = None
    diffUrl: str = None
    baselineUrl: str = None

    def __init__(self, test_run_response: TestRunResponse, api_url: str):
        """
        Converts image names into urls

        :param test_run_response: The response to convert.
        :param api_url: URL to use in image urls
        """
        self.testRunResponse = test_run_response
        self.imageUrl = f'{api_url}/{test_run_response.imageName}'
        self.diffUrl = test_run_response.diffName and f'{api_url}/{test_run_response.diffName}'
        self.baselineUrl = test_run_response.baselineName and f'{api_url}/{test_run_response.baselineName}'


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
