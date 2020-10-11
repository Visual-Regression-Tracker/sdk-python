import json
import logging

import requests

from .types import \
    Config, Build, TestRun, TestRunResponse, TestRunStatus, \
    _to_dict, _from_dict, TestRunResult
from .exceptions import \
    ServerError, TestRunError, VisualRegressionTrackerError


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
            raise VisualRegressionTrackerError("Visual Regression Tracker has not been started")

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

    def _submitTestResult(self, test: TestRun) -> TestRunResponse:
        if not self._isStarted():
            raise VisualRegressionTrackerError("Visual Regression Tracker has not been started")

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
        testRunResult = _from_dict(result, TestRunResponse)

        return testRunResult

    def track(self, test: TestRun):
        result = self._submitTestResult(test)

        switcher = {
            TestRunStatus.NEW: f'No baseline: {result.url}',
            TestRunStatus.UNRESOLVED: f'Difference found: {result.url}'
        }
        error_message = switcher.get(result.status, '')

        if error_message:
            if self.config.enableSoftAssert:
                logging.getLogger(__name__).error(error_message)
            else:
                raise TestRunError(result.status, error_message)

        return TestRunResult(result, self.config.apiUrl)


def _http_request(url: str, method: str, data: dict, headers: dict) -> dict:
    request = getattr(requests, method.lower())
    response = request(url, json=data, headers=headers)
    status = response.status_code
    result = response.json()

    if status == 401:
        raise ServerError('Unauthorized')
    if status == 403:
        raise ServerError('Api key not authenticated')
    if status == 404:
        raise ServerError('Project not found')
    if status >= 400:
        raise ServerError(json.dumps(result, indent=2))

    return result
