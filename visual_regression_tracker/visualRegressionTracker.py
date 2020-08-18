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
        """
        Creates a new VisualRegressionTracker

        :param config: The configuration to use.
        """
        self.config = config
        self.headers = {'apiKey': self.config.apiKey}

    def _isStarted(self):
        return self.buildId is not None and self.projectId is not None

    def start(self):
        data = {
            'branchName': self.config.branchName,
            'project': self.config.project,
        }
        result = _http_request(
            f'{self.config.apiUrl}/builds',
            'post',
            data,
            self.headers
        )
        build = _from_dict(result, Build)
        self.buildId = build.id
        self.projectId = build.projectId

    def stop(self):
        if not self._isStarted():
            raise Exception("Visual Regression Tracker has not been started")

        _http_request(
            f'{self.config.apiUrl}/builds/{self.buildId}',
            'patch',
            data={},
            headers=self.headers
        )
        self.buildId = None
        self.projectId = None

    def __enter__(self):
        """Start the build."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Stop the build."""
        self.stop()

    def _submitTestResult(self, test: TestRun) -> TestRunResult:
        if not self._isStarted():
            raise Exception("Visual Regression Tracker has not been started")

        data = _to_dict(test)
        data.update(
            buildId=self.buildId,
            projectId=self.projectId,
            branchName=self.config.branchName,
        )

        result = _http_request(
            f'{self.config.apiUrl}/test-runs',
            'post',
            data,
            self.headers
        )
        result['status'] = TestRunStatus(result['status'])
        testRunResult = _from_dict(result, TestRunResult)

        return testRunResult

    def track(self, test: TestRun):
        result = self._submitTestResult(test)

        if result.status == TestRunStatus.NEW:
            raise Exception(f'No baseline: {result.url}')
        if result.status == TestRunStatus.UNRESOLVED:
            raise Exception(f'Difference found: {result.url}')


def _http_request(url: str, method: str, data: dict, headers: dict) -> dict:
    request = getattr(requests, method.lower())
    response = request(url, json=data, headers=headers)
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
