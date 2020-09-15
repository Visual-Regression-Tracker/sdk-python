import json
import logging
import re

import pytest

from visual_regression_tracker import \
    Config, VisualRegressionTracker, \
    TestRun, TestRunResult, TestRunStatus, \
    ServerError, TestRunError, VisualRegressionTrackerError
from visual_regression_tracker.types import \
    _to_dict
from visual_regression_tracker.visualRegressionTracker import \
    _http_request

CONFIG = Config(
    apiUrl='http://localhost:4200',
    branchName='develop',
    project='Default project',
    apiKey='CPKVK4JNK24NVNPNGVFQ853HXXEG',
    enableSoftAssert=False,
)


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
    testRun = TestRun(
        name='name',
        imageBase64='image',
        os='os',
        device='device',
        viewport='viewport',
        browser='browser',
    )
    testRunResult = TestRunResult(
        url='url',
        status=TestRunStatus.OK,
        pixelMisMatchCount=12,
        diffPercent=0.12,
        diffTollerancePercent=0,
    )
    vrt._submitTestResult = mocker.Mock(return_value=testRunResult)

    vrt.track(testRun)

    vrt._submitTestResult.assert_called_once_with(testRun)


track_test_data = [
    (
        TestRunResult(
            url='url',
            status=TestRunStatus.NEW,
            pixelMisMatchCount=12,
            diffPercent=0.12,
            diffTollerancePercent=0,
        ),
        'No baseline: url'
    ),
    (
        TestRunResult(
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

    vrt.start()

    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/builds',
        'post',
        {'branchName': CONFIG.branchName, 'project': CONFIG.project},
        {'apiKey': CONFIG.apiKey},
    )

    assert vrt.buildId == buildId
    assert vrt.projectId == projectId


def test__stop__should_stop_build(vrt, mock_request, mocker):
    buildId = '1312'
    vrt.buildId = buildId
    vrt.projectId = 'some id'
    vrt._isStarted = mocker.Mock(return_value=True)

    vrt.stop()

    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/builds/{buildId}',
        'patch',
        data={},
        headers={'apiKey': CONFIG.apiKey},
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
    testRunResult = TestRunResult(
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
        },
        {'apiKey': CONFIG.apiKey},
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


def test__http_request__success(mocker):
    expected = {'a': 'b', 'c': 'd'}

    post = mocker.patch('requests.post')
    response = post.return_value = mocker.Mock()
    response.status_code = 200
    response.json.return_value = expected

    actual = _http_request('url', 'post', {'1': 2}, {2: '3'})

    post.assert_called_once_with('url', json={'1': 2}, headers={2: '3'})
    assert actual == expected


@pytest.mark.parametrize('status_code,response_body,expected_match', [
    (401, {}, 'Unauthorized'),
    (403, {}, 'Api key not authenticated'),
    (404, {}, 'Project not found'),
    (500, '{"message": "exception message"}', json.dumps('{"message": "exception message"}', indent=2)),
])
def test__http_request__maps_status_code(
        mocker, status_code, response_body, expected_match):
    post = mocker.patch('requests.post')
    response = post.return_value = mocker.Mock()
    response.status_code = status_code
    response.json = mocker.Mock(return_value=response_body)
    response.raise_for_status.side_effect = Exception('oh no')

    with pytest.raises(ServerError, match=re.escape(expected_match)):
        _http_request('url', 'post', {'1': 2}, {2: '3'})

    post.assert_called_once_with('url', json={'1': 2}, headers={2: '3'})
