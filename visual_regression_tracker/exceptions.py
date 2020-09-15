from .types import TestRunStatus


class VisualRegressionTrackerError(Exception):
    """An error occurred."""

    pass


class ServerError(VisualRegressionTrackerError):
    """An error occurred on the VisualRegressionTracker server."""

    def __init__(self, *args):
        """Initialises ServerError from server response."""
        super(ServerError, self).__init__(*args)


class TestRunError(VisualRegressionTrackerError):
    """A visual test failed."""

    def __init__(self, status: TestRunStatus, *args):
        """Initialises TestRunError error."""
        self.status = status
        super(TestRunError, self).__init__(*args, status)
