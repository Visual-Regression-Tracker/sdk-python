import pytest
import sys

requires_playwright = pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")

try:
    import playwright
    import visual_regression_tracker.playwright
except:
    pass


@requires_playwright
def test_playwright_imports():
    import playwright


@requires_playwright
def test_visual_regression_tracker_playwright_imports():
    import visual_regression_tracker.playwright
