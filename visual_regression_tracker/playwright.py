import dataclasses
import pathlib

from typing import Union, List, Literal
from playwright.sync_api import FloatRect
from playwright import sync_api
from playwright import async_api
from visual_regression_tracker import \
    Config, IgnoreArea, TestRun, VisualRegressionTracker
from visual_regression_tracker.types import _to_dict


@dataclasses.dataclass
class Agent:
    os: str = None
    device: str = None
    viewport: str = None


@dataclasses.dataclass
class ElementHandleScreenshotOptions:
    timeout: int = None
    type: Literal["jpeg", "png"] = None
    path: Union[str, pathlib.Path] = None
    quality: int = None
    omit_background: bool = None


@dataclasses.dataclass
class PageScreenshotOptions(ElementHandleScreenshotOptions):
    full_page: bool = None
    clip: FloatRect = None


@dataclasses.dataclass
class PageTrackOptions:
    diffTollerancePercent: float = None
    ignoreAreas: List[IgnoreArea] = None
    screenshotOptions: PageScreenshotOptions = None
    agent: Agent = None
    customTags: str = None
    comment: str = None
    merge: bool = None


@dataclasses.dataclass
class ElementHandleTrackOptions:
    diffTollerancePercent: float = None
    ignoreAreas: List[IgnoreArea] = None
    screenshotOptions: ElementHandleScreenshotOptions = None
    agent: Agent = None
    customTags: str = None
    comment: str = None
    merge: bool = None


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
        screenshot = page.screenshot(**_screenshotOptions(options))
        return self.track(self._testRun(name, screenshot, options, _viewport(page)))

    async def trackPageAsync(
            self,
            page: async_api.Page,
            name: str,
            options: PageTrackOptions = None
    ):
        screenshot = await page.screenshot(**_screenshotOptions(options))
        return self.track(self._testRun(name, screenshot, options, _viewport(page)))

    def trackElementHandle(
            self,
            elementHandle: sync_api.ElementHandle,
            name: str,
            options: ElementHandleTrackOptions = None
    ):
        screenshot = elementHandle.screenshot(**_screenshotOptions(options))
        return self.track(self._testRun(name, screenshot, options))

    async def trackElementHandleAsync(
            self,
            elementHandle: async_api.ElementHandle,
            name: str,
            options: ElementHandleTrackOptions = None
    ):
        screenshot = await elementHandle.screenshot(**_screenshotOptions(options))
        return self.track(self._testRun(name, screenshot, options))

    def _testRun(
            self,
            name: str,
            screenshot: bytes,
            options: Union[PageTrackOptions, ElementHandleTrackOptions, None],
            viewport: str = None,
    ) -> TestRun:
        options = options or ElementHandleTrackOptions()
        agent = options.agent or Agent()
        return TestRun(
            name=name,
            imageBuffer=screenshot,
            os=agent.os,
            browser=self.browser.name,
            viewport=viewport or agent.viewport,
            device=agent.device,
            diffTollerancePercent=options.diffTollerancePercent,
            ignoreAreas=options.ignoreAreas,
            customTags=options.customTags,
            comment=options.comment,
            merge=options.merge,
        )


def _screenshotOptions(options) -> dict:
    return _to_dict(options.screenshotOptions) if options and options.screenshotOptions else {}


def _viewport(page) -> str:
    size = page.viewport_size
    return f'{size["width"]}x{size["height"]}' if size else None


class PlaywrightVisualRegressionTracker(PlaywrightMixin, VisualRegressionTracker):
    def __init__(self, browser: Union[sync_api.BrowserType, async_api.BrowserType], config: Config = None):
        """
        Creates a new PlaywrightVisualRegressionTracker

        :param config: The config to use.
        :param browser: the browser type being used by Playwright.
        """
        VisualRegressionTracker.__init__(self, config)
        PlaywrightMixin.__init__(self, browser)
