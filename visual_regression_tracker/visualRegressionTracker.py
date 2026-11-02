import logging

import requests

from .types import \
    Build, TestRun, TestRunResponse, TestRunStatus, \
    _to_dict, _from_dict, TestRunResult
from .exceptions import \
    RequestError, ServerError, TestRunError, VisualRegressionTrackerError
from .config import Config

CONNECT_TIMEOUT_SECONDS = 10


class VisualRegressionTracker:
    config: Config = None
    buildId: str = None
    projectId: str = None
    headers: dict = None

    def __init__(self, config: Config = None):
        """
        Creates a new VisualRegressionTracker

        :param config: The configuration to use.
        """
        self.config = config or Config.default()
        self.headers = {
            'apiKey': self.config.apiKey,
            'project': self.config.project
        }
        self.config.check_complete()

    def _isStarted(self):
        return self.buildId is not None and self.projectId is not None

    def _request(self, method: str, path: str, data: dict) -> dict:
        return _http_request(
            f'{self.config.apiUrl}/{path}',
            method,
            data,
            self.headers,
            (CONNECT_TIMEOUT_SECONDS, self.config.httpTimeoutInSeconds or None),
        )

    def start(self) -> Build:
        data = {
            'ciBuildId': self.config.ciBuildId,
            'branchName': self.config.branchName,
            'project': self.config.project,
        }
        build = _from_dict(self._request('post', 'builds', data), Build)
        self.buildId = build.id
        self.projectId = build.projectId
        return build

    def stop(self):
        if not self._isStarted():
            raise VisualRegressionTrackerError(
                "Visual Regression Tracker has not been started")

        self._request('patch', f'builds/{self.buildId}', {'isRunning': False})
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
            raise VisualRegressionTrackerError(
                "Visual Regression Tracker has not been started")

        data = _to_dict(test)
        data.update(
            buildId=self.buildId,
            projectId=self.projectId,
            branchName=self.config.branchName,
        )

        result = self._request('post', 'test-runs', data)
        testRunResult = _from_dict(result, TestRunResponse)

        return testRunResult

    def track(self, test: TestRun) -> TestRunResult:
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


_HINTS = {
    413: 'the request is larger than BODY_PARSER_JSON_LIMIT on the server; raise it or send a smaller screenshot',
    422: 'the image has more pixels than MAX_IMAGE_PIXELS on the server; raise it or send a smaller screenshot',
}


def _http_request(url: str, method: str, data: dict, headers: dict, timeout: tuple) -> dict:
    request = getattr(requests, method.lower())
    try:
        response = request(url, json=data, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        raise RequestError(url, f'{method.upper()} {url} failed: {type(e).__name__}: {e}') from None
    status = response.status_code

    if status >= 400:
        message = _error_message(response)
        hint = _HINTS.get(status)
        raise ServerError(status, f'{message} (hint: {hint})' if hint else message)

    try:
        return response.json()
    except ValueError:
        raise ServerError(status, f'response from {response.url} is not JSON: {response.text.strip()[:200]}') from None


def _error_message(response) -> str:
    try:
        message = response.json().get('message')
    except (ValueError, AttributeError):
        message = None
    if isinstance(message, list):
        message = ', '.join(map(str, message))
    return message or response.text.strip() or response.reason or 'no error message'
