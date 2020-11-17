
import base64
import dataclasses
import pathlib
import sys

from typing import Union, List
from playwright.page import Page, Literal
from playwright.browser_type import BrowserType
from playwright.element_handle import ElementHandle
from playwright.helper import FloatRect
from visual_regression_tracker.types import \
    _to_dict, Config, IgnoreArea, TestRun
from visual_regression_tracker.visualRegressionTracker import \
    VisualRegressionTracker


@dataclasses.dataclass
class Agent:
  os: str = None
  device: str = None
  viewport: str = None


@dataclasses.dataclass
class PageScreenshotOptions:
    timeout: int = None
    type: Literal["jpeg", "png"] = None
    path: Union[str, pathlib.Path] = None
    quality: int = None
    omitBackground: bool = None
    fullPage: bool = None
    clip: FloatRect = None


@dataclasses.dataclass
class PageTrackOptions:
  diffTollerancePercent: float = None
  ignoreAreas: List[IgnoreArea] = None
  screenshotOptions: PageScreenshotOptions = None
  agent: Agent = None


@dataclasses.dataclass
class ElementHandleScreenshotOptions:
    timeout: int = None
    type: Literal["jpeg", "png"] = None
    path: Union[str, pathlib.Path] = None
    quality: int = None
    omitBackground: bool = None


@dataclasses.dataclass
class ElementHandleTrackOptions:
  diffTollerancePercent: float = None
  ignoreAreas: List[IgnoreArea] = None
  screenshotOptions: ElementHandleScreenshotOptions = None
  agent: Agent = None


class PlaywrightVisualRegressionTracker:
    def __init__(
        self,
        config: Config,
        browser: BrowserType
    ):
        self.vrt = VisualRegressionTracker(config)
        self.browser = browser

    def start(self):
        self.vrt.start()

    def stop(self):
        self.vrt.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def trackPage(self, page: Page, name: str, options: PageTrackOptions):
        viewportSize = page.viewportSize()
        
        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = page.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot)

        self.vrt.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            f'{viewportSize["width"]}x{viewportSize["height"]}' if viewportSize else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))

    def trackElementHandle(self, elementHandle: ElementHandle, name: str, options: ElementHandleTrackOptions):
        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = elementHandle.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot)

        self.vrt.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            options.agent.viewport if options and options.agent else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))


if __name__ == '__main__':

    from playwright import sync_playwright
    from visual_regression_tracker import Config, TestRun
    from visual_regression_tracker.playwright import PlaywrightVisualRegressionTracker, PageTrackOptions

    config = Config()

    playwright = sync_playwright().start()
    browserType = playwright.chromium

    with PlaywrightVisualRegressionTracker(config, browserType) as vrt:
        browser = browserType.launch(headless=False)
        page = browser.newPage()
        page.goto('https://www.python.org/')

        imageName = 'Python Homepage'
        options = PageTrackOptions(
            screenshotOptions=PageScreenshotOptions(
                path='/tmp/bob.png',
            ),
        )
        vrt.trackPage(
            page,
            imageName,
            options
        )

