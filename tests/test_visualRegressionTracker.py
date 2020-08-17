import pytest
from visual_regression_tracker import \
    Config, VisualRegressionTracker, \
    TestRun, TestRunResult, TestRunStatus
from visual_regression_tracker.visualRegressionTracker import \
    _http_request
from visual_regression_tracker.types import \
    _to_dict

CONFIG = Config(
    apiUrl='http://localhost:4200',
    branchName='develop',
    project='Default project',
    apiKey='CPKVK4JNK24NVNPNGVFQ853HXXEG',
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

    assert vrt._isStarted() == expectedResult


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


def test__track__should_track_no_baseline(vrt, mocker):
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
        status=TestRunStatus.NEW,
        pixelMisMatchCount=12,
        diffPercent=0.12,
        diffTollerancePercent=0,
    )
    vrt._submitTestResult = mocker.Mock(return_value=testRunResult)

    with pytest.raises(Exception, match='No baseline: url'):
        vrt.track(testRun)


def test__track__should_track_difference(vrt, mocker):
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
        status=TestRunStatus.UNRESOLVED,
        pixelMisMatchCount=12,
        diffPercent=0.12,
        diffTollerancePercent=0,
    )
    vrt._submitTestResult = mocker.Mock(return_value=testRunResult)

    with pytest.raises(Exception, match='Difference found: url'):
        vrt.track(testRun)


def test__start__should_start_build(vrt, mock_request):
    buildId = '1312'
    projectId = 'asd'
    mock_request.return_value = {'id': buildId, 'projectId': projectId}

    vrt._start()

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
    vrt._isStarted = mocker.Mock(return_value=True)

    vrt._stop()

    mock_request.assert_called_once_with(
        f'{CONFIG.apiUrl}/builds/{buildId}',
        'patch',
        headers={'apiKey': CONFIG.apiKey},
    )


def test__stop__should_throw_not_started(vrt, mock_request, mocker):
    vrt._isStarted = mocker.Mock(return_value=False)

    with pytest.raises(Exception, match='Visual Regression Tracker has not been started'):
        vrt._stop()


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

    with pytest.raises(Exception, match='Visual Regression Tracker has not been started'):
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


def test__http_request__checks_status(mocker):
    post = mocker.patch('requests.post')
    response = post.return_value = mocker.Mock()
    response.status_code = 200
    response.raise_for_status.side_effect = Exception('oh no')

    with pytest.raises(Exception, match='oh no'):
        _http_request('url', 'post', {'1': 2}, {2: '3'})

    post.assert_called_once_with('url', json={'1': 2}, headers={2: '3'})


@pytest.mark.parametrize('status_code,expected_match', [
    (401, 'Unauthorized'),
    (403, 'Api key not authenticated'),
    (404, 'Project not found'),
])
def test__http_request__maps_status_code(
        mocker, status_code, expected_match):
    post = mocker.patch('requests.post')
    response = post.return_value = mocker.Mock()
    response.status_code = status_code
    response.json.side_effect = Exception('oh no')
    response.raise_for_status.side_effect = Exception('oh no')

    with pytest.raises(Exception, match=expected_match):
        _http_request('url', 'post', {'1': 2}, {2: '3'})

    post.assert_called_once_with('url', json={'1': 2}, headers={2: '3'})
