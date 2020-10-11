"""
Python SDK for Visual Regression Tracker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open source, self hosted solution for visual testing and managing results of visual testing.

Basic usage:
    from visual_regression_tracker import VisualRegressionTracker, Config, TestRun
    config = Config(
        apiUrl='http://localhost:4200',
        project='Default project',
        apiKey='tXZVHX0EA4YQM1MGDD',
        branchName='develop',
    )
    with VisualRegressionTracker(config) as vrt:
        vrt.track(TestRun(
            name='Image name',
            imageBase64=image,
        ))
"""

from .types import Config, Build, TestRun, TestRunResponse, TestRunStatus
from .exceptions import VisualRegressionTrackerError, ServerError, TestRunError
from .visualRegressionTracker import VisualRegressionTracker

__all__ = [
    'Config', 'Build', 'TestRun', 'TestRunResponse', 'TestRunStatus',
    'VisualRegressionTrackerError', 'ServerError', 'TestRunError',
    'VisualRegressionTracker',
]
