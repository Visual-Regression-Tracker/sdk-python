from .types import TestRunStatus


class VisualRegressionTrackerError(Exception):
    """An error occurred."""

    pass


class ServerError(VisualRegressionTrackerError):
    """The VisualRegressionTracker server answered with an HTTP error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super(ServerError, self).__init__(f'HTTP {status_code}: {message}')


class TestRunError(VisualRegressionTrackerError):
    """A visual test failed."""

    def __init__(self, status: TestRunStatus, *args):
        """Initialises TestRunError error."""
        self.status = status
        super(TestRunError, self).__init__(*args, status)


class MissingConfigurationError(VisualRegressionTrackerError):
    """VRT Configuration is incomplete."""

    def __init__(self, field, *args):
        self.field = field
        super(MissingConfigurationError, self).__init__(*args, field)
