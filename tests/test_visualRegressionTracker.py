import dataclasses
import json
import logging
import re

import pytest
import requests

from visual_regression_tracker import \
    Build, Config, IgnoreArea, VisualRegressionTracker, \
    TestRun, TestRunResponse, TestRunStatus, \
    RequestError, ServerError, TestRunError, VisualRegressionTrackerError
from visual_regression_tracker.types import \
    _to_dict
from visual_regression_tracker.visualRegressionTracker import \
    _http_request

CONFIG = Config(
    apiUrl='http://localhost:4200',
    ciBuildId='CI Build Id',
    branchName='develop',
    project='Default project',
    apiKey='CPKVK4JNK24NVNPNGVFQ853HXXEG',
    enableSoftAssert=False,
    httpTimeoutInSeconds=12,
)
HEADERS = {
    'apiKey': CONFIG.apiKey,
    'project': CONFIG.project
}
TIMEOUT = (10, CONFIG.httpTimeoutInSeconds)


@pytest.fixture
def mock_request(mocker):
    yield mocker.patch(
        'visual_regression_tracker.visualRegressionTracker'
        '._http_request')


@pytest.fixture
def vrt():
    yield VisualRegressionTracker(CONFIG)


@pytest.mark.parametrize('buildId,projectId,expectedResult', [
    (None, None, False),
    (None, "some", False),
    ("some", None, False),
    ("some", "some", True),
])
def test__isStarted(vrt, buildId, projectId, expectedResult):
    vrt.buildId = buildId
    vrt.projectId = projectId

    result = vrt._isStarted()

    assert result == expectedResult


def test__track__should_track_success(vrt, mocker):
    test_run = TestRun(
        name='name',
        imageBase64='image',
        os='os',
        device='device',
        viewport='viewport',
        browser='browser',
    )
    test_run_response = TestRunResponse(
        url='url',
        status=TestRunStatus.OK,
        pixelMisMatchCount=12,
        diffPercent=0.12,
        diffTollerancePercent=0,
        imageName='imageName',
        diffName='diffName',
        baselineName='baselineName'
    )
    vrt._submitTestResult = mocker.Mock(return_value=test_run_response)

    test_run_result = vrt.track(test_run)

    vrt._submitTestResult.assert_called_once_with(test_run)
    assert test_run_result.testRunResponse == test_run_response
    assert test_run_result.imageUrl == f'{CONFIG.apiUrl}/images/{test_run_response.imageName}'
    assert test_run_result.diffUrl == f'{CONFIG.apiUrl}/images/{test_run_response.diffName}'
    assert test_run_result.baselineUrl == f'{CONFIG.apiUrl}/images/{test_run_response.baselineName}'


@pytest.mark.parametrize('status', [
    TestRunStatus.OK,
    TestRunStatus.APPROVED,
    TestRunStatus.AUTO_APPROVED,
    TestRunStatus.FAILED,
    TestRunStatus.UNKNOWN,
])
def test__track__should_pass_statuses_other_than_new_and_unresolved(status, vrt, mocker, caplog):
    vrt._submitTestResult = mocker.Mock(return_value=TestRunResponse(url='url', status=status, imageName='imageName'))

    vrt.track(TestRun())

    assert caplog.record_tuples == []


def test__track__should_accept_autoApproved_from_server(vrt, mock_request):
    vrt.buildId = '1312'
    vrt.projectId = 'asd'
    mock_request.return_value = {'url': 'url', 'status': 'autoApproved', 'imageName': 'imageName'}

    result = vrt.track(TestRun(name='name'))

    assert result.testRunResponse.status == TestRunStatus.AUTO_APPROVED


track_test_data = [
    (
        TestRunResponse(
            url='url',
            status=TestRunStatus.NEW,
            pixelMisMatchCount=12,
            diffPercent=0.12,
            diffTollerancePercent=0,
        ),
        'No baseline: url'
    ),
    (
        TestRunResponse(
            url='url',
            status=TestRunStatus.UNRESOLVED,
            pixelMisMatchCount=12,
            diffPercent=0.12,
            diffTollerancePercent=0,
        ),
        'Difference found: url'
    )
]


@pytest.mark.parametrize("test_run_result, expected_error", track_test_data)
def test__track__should_raise_exception(test_run_result, expected_error, vrt, mocker):
    vrt.config.enableSoftAssert = False
    vrt._submitTestResult = mocker.Mock(return_value=test_run_result)

    with pytest.raises(TestRunError, match=expected_error):
        vrt.track(TestRun())


@pytest.mark.parametrize("test_run_result, expected_error", track_test_data)
def test__track__should_log_error(test_run_result, expected_error, vrt, mocker, caplog):
    vrt.config.enableSoftAssert = True
    vrt._submitTestResult = mocker.Mock(return_value=test_run_result)

    vrt.track(TestRun())

    assert caplog.record_tuples == [(
        "visual_regression_tracker.visualRegressionTracker",
        logging.ERROR,
        expected_error
    )]


def test__start__should_start_build(vrt, mock_request):
    buildId = '1312'
    projectId = 'asd'
    mock_request.return_value = {'id': buildId, 'projectId': projectId}

    build = vrt.start()

    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/builds',
        'post',
        {
            'ciBuildId': CONFIG.ciBuildId,
            'branchName': CONFIG.branchName,
            'project': CONFIG.project
        },
        HEADERS,
        TIMEOUT,
    )

    assert build == Build(buildId, projectId)
    assert vrt.buildId == buildId
    assert vrt.projectId == projectId


def test__start__should_not_double_the_slash_after_apiUrl(mock_request):
    vrt = VisualRegressionTracker(dataclasses.replace(CONFIG, apiUrl='http://localhost:4200/'))
    mock_request.return_value = {'id': '1312', 'projectId': 'asd'}

    vrt.start()

    assert mock_request.call_args[0][0] == 'http://localhost:4200/builds'


def test__request__treats_zero_timeout_as_no_read_timeout(mock_request):
    vrt = VisualRegressionTracker(dataclasses.replace(CONFIG, httpTimeoutInSeconds=0))
    mock_request.return_value = {'id': '1312', 'projectId': 'asd'}

    vrt.start()

    assert mock_request.call_args[0][4] == (10, None)


def test__stop__should_stop_build(vrt, mock_request, mocker):
    buildId = '1312'
    vrt.buildId = buildId
    vrt.projectId = 'some id'
    vrt._isStarted = mocker.Mock(return_value=True)

    vrt.stop()

    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/builds/{buildId}',
        'patch',
        {'isRunning': False},
        HEADERS,
        TIMEOUT,
    )
    assert vrt.buildId is None
    assert vrt.projectId is None


def test__stop__should_throw_not_started(vrt, mock_request, mocker):
    vrt._isStarted = mocker.Mock(return_value=False)

    with pytest.raises(VisualRegressionTrackerError,
                       match='Visual Regression Tracker has not been started'):
        vrt.stop()


def test__enter__should_start_build(vrt, mocker):
    vrt.start = mocker.Mock()
    vrt.__enter__()
    vrt.start.assert_called_once()


def test__exit__should_stop_build(vrt, mocker):
    vrt.stop = mocker.Mock()
    vrt.__exit__(None, None, None)
    vrt.stop.assert_called_once()


def test__contextmanager__starts_and_stops_build(vrt, mocker):
    vrt.start = mocker.Mock()
    vrt.stop = mocker.Mock()

    with vrt as actual:
        assert vrt == actual
        vrt.start.assert_called_once()
        vrt.stop.assert_not_called()

    vrt.start.assert_called_once()
    vrt.stop.assert_called_once()


def test__submitTestResults__should_submit_test_run(vrt, mock_request):
    testRunResult = TestRunResponse(
        url='url',
        status=TestRunStatus.UNRESOLVED,
        pixelMisMatchCount=12,
        diffPercent=0.12,
        diffTollerancePercent=0,
    )
    testRun = TestRun(
        name='name',
        imageBase64='image',
        os='os',
        device='device',
        viewport='viewport',
        browser='browser',
        ignoreAreas=[IgnoreArea(1, 2, 3, 4)]
    )
    buildId = '1312'
    projectId = 'asd'
    vrt.buildId = buildId
    vrt.projectId = projectId

    mock_request.return_value = _to_dict(testRunResult)

    result = vrt._submitTestResult(testRun)

    assert result == testRunResult
    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/test-runs',
        'post',
        {
            'name': testRun.name,
            'imageBase64': testRun.imageBase64,
            'os': testRun.os,
            'browser': testRun.browser,
            'viewport': testRun.viewport,
            'device': testRun.device,
            'buildId': buildId,
            'projectId': projectId,
            'branchName': CONFIG.branchName,
            'ignoreAreas': [
                {
                    'x': 1,
                    'y': 2,
                    'width': 3,
                    'height': 4,
                }
            ]
        },
        HEADERS,
        TIMEOUT,
    )


def test__submitTestResults__should_throw_not_started(vrt, mocker):
    testRun = TestRun(
        name='name',
        imageBase64='image',
        os='os',
        device='device',
        viewport='viewport',
        browser='browser',
    )
    vrt._isStarted = mocker.Mock(return_value=False)

    with pytest.raises(VisualRegressionTrackerError,
                       match='Visual Regression Tracker has not been started'):
        vrt._submitTestResult(testRun)


def mock_response(mocker, status_code, body=None, text='', reason=''):
    response = mocker.Mock()
    response.url = 'http://vrt/builds'
    response.status_code = status_code
    response.reason = reason
    if body is None:
        response.text = text
        response.json.side_effect = ValueError('Expecting value')
    else:
        response.text = json.dumps(body)
        response.json.return_value = body
    return response


def test__http_request__success(mocker):
    expected = {'a': 'b', 'c': 'd'}
    post = mocker.patch('requests.post', return_value=mock_response(mocker, 200, expected))

    actual = _http_request('url', 'post', {'1': 2}, {2: '3'}, 7)

    post.assert_called_once_with('url', json={'1': 2}, headers={2: '3'}, timeout=7)
    assert actual == expected


@pytest.mark.parametrize('status_code,body,text,reason,expected_message', [
    (401, {'statusCode': 401, 'message': 'Unauthorized'}, '', '', 'Unauthorized'),
    (403, {'message': 'You do not have permission to perform this operation.'}, '', '',
     'You do not have permission to perform this operation.'),
    (404, {'statusCode': 404, 'path': '/builds/1', 'name': 'NotFoundException', 'message': 'Build not found'}, '', '',
     'Build not found'),
    (400, {'statusCode': 400, 'message': ['name must be a string', 'branchName must be a string']}, '', '',
     'name must be a string, branchName must be a string'),
    (502, None, '<html>Bad Gateway</html>', 'Bad Gateway', '<html>Bad Gateway</html>'),
    (503, None, '', 'Service Unavailable', 'Service Unavailable'),
    (500, {'error': 'no message field'}, '', '', '{"error": "no message field"}'),
    (400, {'message': [{'property': 'name'}]}, '', '', "{'property': 'name'}"),
])
def test__http_request__raises_server_error_with_server_message(
        mocker, status_code, body, text, reason, expected_message):
    mocker.patch('requests.post', return_value=mock_response(mocker, status_code, body, text, reason))

    with pytest.raises(ServerError) as error:
        _http_request('url', 'post', {}, {}, 30)

    assert error.value.status_code == status_code
    assert error.value.message == expected_message
    assert str(error.value) == f'HTTP {status_code}: {expected_message}'


def test__http_request__raises_server_error_on_success_without_json(mocker):
    mocker.patch('requests.post', return_value=mock_response(mocker, 200, None, '<html>Sign in</html>'))

    with pytest.raises(ServerError, match='http://vrt/builds is not JSON: <html>Sign in</html>') as error:
        _http_request('url', 'post', {}, {}, 30)

    assert error.value.status_code == 200
    assert error.value.__suppress_context__


@pytest.mark.parametrize('exception', [
    requests.exceptions.ReadTimeout('Read timed out. (read timeout=360)'),
    requests.exceptions.ConnectionError('Failed to establish a new connection'),
])
def test__http_request__wraps_request_exceptions_without_headers(mocker, exception):
    mocker.patch('requests.post', side_effect=exception)

    with pytest.raises(RequestError) as error:
        _http_request('http://vrt/test-runs', 'post', {}, {'apiKey': 'secret-key'}, (10, 360))

    assert error.value.url == 'http://vrt/test-runs'
    assert str(error.value) == f'POST http://vrt/test-runs failed: {type(exception).__name__}: {exception}'
    assert 'secret-key' not in str(error.value)
    assert error.value.__cause__ is None and error.value.__suppress_context__


@pytest.mark.parametrize('status_code,body,hint', [
    (413, None, 'BODY_PARSER_JSON_LIMIT'),
    (422, {'message': 'Image is 20000x20000 (400000000 pixels), above MAX_IMAGE_PIXELS=100000000'}, 'MAX_IMAGE_PIXELS'),
])
def test__http_request__adds_hint_for_image_limits(mocker, status_code, body, hint):
    mocker.patch('requests.post', return_value=mock_response(mocker, status_code, body, 'request entity too large'))

    with pytest.raises(ServerError, match=re.escape(hint)) as error:
        _http_request('url', 'post', {}, {}, 30)

    assert error.value.status_code == status_code
