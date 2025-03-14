import dataclasses
import enum
import typing
import dacite


@dataclasses.dataclass
class IgnoreArea:
    x: int = None
    y: int = None
    width: int = None
    height: int  = None


@dataclasses.dataclass
class TestRun:
    name: str = None
    imageBase64: str = None
    os: str = None
    browser: str = None
    viewport: str = None
    device: str = None
    diffTollerancePercent: float = None
    ignoreAreas: typing.List[IgnoreArea] = None


@dataclasses.dataclass
class Build:
    id: str = None
    projectId: str = None


class TestRunStatus(enum.Enum):
    NEW = 'new'
    OK = 'ok'
    UNRESOLVED = 'unresolved'
    AUTO_APPROVED = 'autoApproved'


@dataclasses.dataclass
class TestRunResponse:
    id: str = None
    imageName: str = None
    diffName: typing.Optional[str] = None
    baselineName: typing.Optional[str] = None
    url: str = None
    merge: bool = False
    status: TestRunStatus = None
    pixelMisMatchCount: typing.Optional[float] = None
    diffPercent: typing.Optional[float] = None
    diffTollerancePercent: typing.Optional[float] = None


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
    def dict_factory(key_values):
        return dict(kv for kv in key_values if kv[1] is not None)

    data = dataclasses.asdict(obj, dict_factory=dict_factory)
    return data


def _from_dict(data, clazz):
    obj = dacite.from_dict(clazz, data)
    return obj
