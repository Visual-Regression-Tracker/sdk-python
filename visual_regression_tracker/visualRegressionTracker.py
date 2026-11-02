import email.utils
import json
import logging
import pathlib
import time

import requests

from .types import \
    Build, TestRun, TestRunResponse, TestRunStatus, \
    _to_dict, _from_dict, TestRunResult
from .exceptions import \
    RequestError, ServerError, TestRunError, VisualRegressionTrackerError
from .config import Config

CONNECT_TIMEOUT_SECONDS = 10
MAX_RETRIES_ON_503 = 3
MAX_RETRY_AFTER_SECONDS = 60
IMAGE_FIELDS = ('imageBase64', 'imagePath', 'imageBuffer')


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

    def _request(self, method: str, path: str, data: dict, **kwargs) -> dict:
        return _http_request(
            f'{self.config.apiUrl}/{path}',
            method,
            data,
            self.headers,
            (CONNECT_TIMEOUT_SECONDS, self.config.httpTimeoutInSeconds or None),
            **kwargs,
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

        images = [field for field in IMAGE_FIELDS if getattr(test, field) is not None]
        if len(images) > 1:
            raise ValueError(f'TestRun takes only one of imageBase64, imagePath and imageBuffer, got {images}')

        data = _to_dict(test)
        data.update(
            buildId=self.buildId,
            projectId=self.projectId,
            branchName=self.config.branchName,
        )
        if self.config.sourceBranch:
            data['sourceBranch'] = self.config.sourceBranch

        if test.imagePath is None and test.imageBuffer is None:
            result = self._request('post', 'test-runs', data)
        else:
            fields, image = _multipart(data)
            result = self._request('post', 'test-runs/multipart', fields, files={'image': image})
        return _from_dict(result, TestRunResponse)

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


def _multipart(data: dict) -> tuple:
    path = data.pop('imagePath', None)
    if path is None:
        filename, image = 'image.png', data.pop('imageBuffer')
    else:
        filename, image = pathlib.Path(path).name, pathlib.Path(path).read_bytes()
    fields = {key: _form_value(value) for key, value in data.items()}
    return fields, (filename, image, 'image/png')


def _form_value(value) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def _hint(status: int, url: str, retries: int):
    if status == 413 and url.endswith('/test-runs/multipart'):
        return 'the image is larger than MULTIPART_FILE_SIZE_LIMIT on the server; raise it or send a smaller screenshot'
    if status == 413:
        return ('the request is larger than BODY_PARSER_JSON_LIMIT on the server; '
                'track the image with imagePath or imageBuffer (multipart), raise the limit, or send a smaller screenshot')
    if status == 422:
        return 'the image has more pixels than MAX_IMAGE_PIXELS on the server; raise it or send a smaller screenshot'
    if status == 503 and retries:
        return f'the server is busy; retried {retries} times after its Retry-After'
    return None


def _http_request(url: str, method: str, data: dict, headers: dict, timeout: tuple, files: dict = None) -> dict:
    request = getattr(requests, method.lower())
    body = {'data': data, 'files': files} if files else {'json': data}
    retries = 0
    while True:
        try:
            response = request(url, **body, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            raise RequestError(url, f'{method.upper()} {url} failed: {type(e).__name__}: {e}') from None
        status = response.status_code
        delay = _retry_after(response) if status == 503 else None
        if delay is None or retries == MAX_RETRIES_ON_503:
            break
        retries += 1
        logging.getLogger(__name__).warning(
            '%s %s: HTTP 503, retry %d of %d in %g s', method.upper(), url, retries, MAX_RETRIES_ON_503, delay)
        time.sleep(delay)

    if status >= 400:
        message = _error_message(response)
        hint = _hint(status, url, retries)
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


def _retry_after(response):
    value = response.headers.get('Retry-After', '').strip()
    if value.isdigit():
        seconds = int(value)
    else:
        try:
            seconds = email.utils.parsedate_to_datetime(value).timestamp() - time.time()
        except (TypeError, ValueError):
            seconds = None
    return seconds if seconds is not None and 0 <= seconds <= MAX_RETRY_AFTER_SECONDS else None
