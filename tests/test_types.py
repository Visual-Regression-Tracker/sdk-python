import pytest

from visual_regression_tracker.types import \
    Build, _to_dict, _from_dict, TestRunResponse, TestRunStatus, TestRunResult


@pytest.mark.parametrize('data, clazz, expected', [
    ({'id': 1, 'projectId': 2}, Build, Build(1, 2)),
    ({}, Build, Build(None, None)),
    ({'id': 1, 'wrong': 2}, Build, Build(1, None)),
    ({'wrong': 1, 'projectId': 2}, Build, Build(None, 2)),
])
def test__from_dict(data, clazz, expected):
    actual = _from_dict(data, clazz)
    assert actual == expected


@pytest.mark.parametrize('obj, expected', [
    (Build(1, 2), {'id': 1, 'projectId': 2}),
    (Build(1), {'id': 1}),
    (Build(), {}),
    (Build(None, 2), {'projectId': 2}),
])
def test__to_dict(obj, expected):
    actual = _to_dict(obj)
    assert actual == expected


def test__TestRunResult_all_images():
    test_run_response = TestRunResponse(
        "someId",
        "imageName",
        "diffName",
        "baselineName",
    )

    result = TestRunResult(test_run_response, "http://localhost")

    assert result.testRunResponse == test_run_response
    assert result.imageUrl == "http://localhost/imageName"
    assert result.diffUrl == "http://localhost/diffName"
    assert result.baselineUrl == "http://localhost/baselineName"


def test__TestRunResult_only_required_images():
    test_run_response = TestRunResponse(
        "someId",
        "imageName",
        None,
        None,
    )

    result = TestRunResult(test_run_response, "http://localhost")

    assert result.testRunResponse == test_run_response
    assert result.imageUrl == "http://localhost/imageName"
    assert result.diffUrl is None
    assert result.baselineUrl is None
