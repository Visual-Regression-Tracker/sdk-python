
import base64
import dataclasses
import pathlib

from typing import Union, List
from playwright.sync_api import Literal, FloatRect
from playwright import sync_api
from playwright import async_api
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


class PlaywrightMixin:
    def __init__(self, browser: Union[sync_api.BrowserType, async_api.BrowserType]):
        """Initialise the playwright mixin."""
        self.browser = browser

    def trackPage(
        self,
        page: sync_api.Page,
        name: str,
        options: PageTrackOptions = None
    ):
        viewportSize = page.viewportSize()
        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = page.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot).decode('ascii')

        self.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            f'{viewportSize["width"]}x{viewportSize["height"]}' if viewportSize else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))

    async def trackPageAsync(
        self,
        page: async_api.Page,
        name: str,
        options: PageTrackOptions = None
    ):
        viewportSize = page.viewportSize()

        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = await page.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot).decode('ascii')

        self.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            f'{viewportSize["width"]}x{viewportSize["height"]}' if viewportSize else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))

    def trackElementHandle(
        self,
        elementHandle: sync_api.ElementHandle,
        name: str,
        options: ElementHandleTrackOptions = None
    ):
        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = elementHandle.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot).decode('ascii')

        self.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            options.agent.viewport if options and options.agent else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))

    async def trackElementHandleAsync(
        self,
        elementHandle: async_api.ElementHandle,
        name: str,
        options: ElementHandleTrackOptions = None
    ):
        screenshotOptions = _to_dict(options.screenshotOptions) if options else {}
        screenshot = await elementHandle.screenshot(**screenshotOptions)
        imageBase64 = base64.b64encode(screenshot).decode('ascii')

        self.track(TestRun(
            name,
            imageBase64,
            options.agent.os if options and options.agent else None,
            self.browser.name,
            options.agent.viewport if options and options.agent else None,
            options.agent.device if options and options.agent else None,
            options.diffTollerancePercent if options else None,
            options.ignoreAreas if options else None,
        ))


class PlaywrightVisualRegressionTracker(PlaywrightMixin, VisualRegressionTracker):
    def __init__(self, config: Config, browser: Union[sync_api.BrowserType, async_api.BrowserType]):
        """
        Creates a new PlaywrightVisualRegressionTracker

        :param config: The config to use.
        :param browser: the browser type being used by Playwright.
        """
        VisualRegressionTracker.__init__(self, config)
        PlaywrightMixin.__init__(self, browser)
