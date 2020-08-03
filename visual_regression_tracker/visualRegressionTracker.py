import requests
from .types import \
    Config, Build, TestRun, TestRunResult, TestRunStatus, \
    _to_dict, _from_dict


class VisualRegressionTracker:
    config: Config = None
    buildId: str = None
    projectId: str = None
    headers: dict = None

    def __init__(self, config: Config):
        self.config = config
        self.headers = {'apiKey': self.config.apiKey}

    def _startBuild(self):
        if self.buildId:
            return

        data = {
            'branchName': self.config.branchName,
            'project': self.config.project,
        }
        result = _http_post_json(
            f'{self.config.apiUrl}/builds',
            data,
            self.headers
        )
        build = _from_dict(result, Build)

        if build.id:
            self.buildId = build.id
        else:
            raise Exception("Build id is not defined")

        if build.projectId:
            self.projectId = build.projectId
        else:
            raise Exception("Project id is not defined")

    def _submitTestResult(self, test: TestRun) -> TestRunResult:
        data = _to_dict(test)
        data.update(
            buildId=self.buildId,
            projectId=self.projectId,
            branchName=self.config.branchName,
        )

        result = _http_post_json(
            f'{self.config.apiUrl}/test-runs',
            data,
            self.headers
        )
        result['status'] = TestRunStatus(result['status'])
        testRunResult = _from_dict(result, TestRunResult)

        return testRunResult

    def track(self, test: TestRun):
        self._startBuild()

        result = self._submitTestResult(test)

        if result.status == TestRunStatus.NEW:
            raise Exception(f'No baseline: {result.url}')
        if result.status == TestRunStatus.UNRESOLVED:
            raise Exception(f'Difference found: {result.url}')


def _http_post_json(url: str, data: dict, headers: dict) -> dict:
    response = requests.post(url, json=data, headers=headers)
    status = response.status_code

    if status == 401:
        raise Exception('Unauthorized')
    if status == 403:
        raise Exception('Api key not authenticated')
    if status == 404:
        raise Exception('Project not found')

    response.raise_for_status()
    result = response.json()
    return result
