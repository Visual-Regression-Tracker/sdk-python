import asyncio
import pytest
import base64
import binascii
import visual_regression_tracker.types
playwright = pytest.importorskip('playwright')
import visual_regression_tracker.playwright


CONFIG = visual_regression_tracker.types.Config(
    apiUrl='https://server/',
    ciBuildId='CI Build Id',
    branchName='Branch Name',
    project='Project',
    apiKey='API Key',
    enableSoftAssert=False,
)


@pytest.fixture
def pvrt(sync_browserType, mocker):
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'start')
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'track')
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'stop')
    pvrt = visual_regression_tracker.playwright.PlaywrightVisualRegressionTracker(CONFIG, sync_browserType)
    return pvrt


def test_pvrt_extends_vrt(sync_browserType):
    pvrt = visual_regression_tracker.playwright.PlaywrightVisualRegressionTracker(CONFIG, sync_browserType)
    assert isinstance(pvrt, visual_regression_tracker.VisualRegressionTracker)


def test_pvrt_extends_mixin(sync_browserType):
    pvrt = visual_regression_tracker.playwright.PlaywrightVisualRegressionTracker(CONFIG, sync_browserType)
    assert isinstance(pvrt, visual_regression_tracker.playwright.PlaywrightMixin)


def test_pvrt_init_saves_parameters(pvrt, sync_browserType):
    assert pvrt.browser == sync_browserType
    assert pvrt.config == CONFIG


def test_pvrt_calls_start_and_stop(pvrt):
    with pvrt:
        pvrt.start.assert_called_once()

    pvrt.start.assert_called_once()
    pvrt.stop.assert_called_once()


def test_pvrt_trackPage__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
        pvrt.trackPage(None, 'name')


@pytest.fixture(scope='session')
def sync_playwright():
    with playwright.sync_playwright() as p:
        yield p


@pytest.fixture(scope='session')
def sync_browserType(sync_playwright):
    return sync_playwright.chromium


@pytest.fixture(scope='session')
def sync_page(sync_browserType):
    browser = sync_browserType.launch(headless=True)
    try:
        page = browser.newPage()
        page.setViewportSize(1024, 768)
        page.goto('https://google.com')
        yield page
    finally:
        browser.close()


def test_pvrt_trackPage__default_options(pvrt, sync_page, sync_browserType):
    pvrt.trackPage(sync_page, 'image name')

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os is None
    assert testRun.browser == sync_browserType.name
    assert testRun.viewport == '1024x768'
    assert testRun.device is None
    assert testRun.diffTollerancePercent is None
    assert testRun.ignoreAreas is None


def test_pvrt_trackPage(pvrt, sync_page, sync_browserType):
    pvrt.trackPage(
        sync_page,
        'image name',
        visual_regression_tracker.playwright.PageTrackOptions(
            diffTollerancePercent=10,
            ignoreAreas=[
                visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
            ],
            screenshotOptions=visual_regression_tracker.playwright.PageScreenshotOptions(
                timeout=1000,
                type='jpeg',
                path=None,
                quality=100,
                omitBackground=False,
                fullPage=True,
            ),
            agent=visual_regression_tracker.playwright.Agent(
                os='os',
                device='device',
                viewport='123x345',
            ),
        ),
    )

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os == 'os'
    assert testRun.browser == sync_browserType.name
    assert testRun.viewport == '1024x768'
    assert testRun.device == 'device'
    assert testRun.diffTollerancePercent == 10
    assert testRun.ignoreAreas == [
        visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
    ]


def test_pvrt_trackElementHandle__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
        pvrt.trackElementHandle(None, 'name')


def test_pvrt_trackElementHandle__default_options(pvrt, sync_elementHandle, sync_browserType):
    pvrt.trackElementHandle(sync_elementHandle, 'image name')

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os is None
    assert testRun.browser == sync_browserType.name
    assert testRun.viewport is None
    assert testRun.device is None
    assert testRun.diffTollerancePercent is None
    assert testRun.ignoreAreas is None


def test_pvrt_trackElementHandle(pvrt, sync_elementHandle, sync_browserType):
    pvrt.trackElementHandle(
        sync_elementHandle,
        'image name',
        visual_regression_tracker.playwright.ElementHandleTrackOptions(
            diffTollerancePercent=10,
            ignoreAreas=[
                visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
            ],
            screenshotOptions=visual_regression_tracker.playwright.ElementHandleScreenshotOptions(
                timeout=1000,
                type='jpeg',
                path=None,
                quality=100,
                omitBackground=False,
            ),
            agent=visual_regression_tracker.playwright.Agent(
                os='os',
                device='device',
                viewport='123x345',
            ),
        ),
    )

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os == 'os'
    assert testRun.browser == sync_browserType.name
    assert testRun.viewport == '123x345'
    assert testRun.device == 'device'
    assert testRun.diffTollerancePercent == 10
    assert testRun.ignoreAreas == [
        visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
    ]


@pytest.fixture
def sync_elementHandle(sync_page):
    return sync_page.querySelector('form')


@pytest.fixture(scope='session')
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture(scope='session')
async def async_playwright():
    async with playwright.async_playwright() as p:
        yield p


@pytest.fixture(scope='session')
async def async_browserType(async_playwright):
    return async_playwright.chromium


@pytest.fixture(scope='session')
async def async_page(async_browserType):
    browser = await async_browserType.launch(headless=True)
    try:
        page = await browser.newPage()
        await page.setViewportSize(1024, 768)
        await page.goto('https://google.com')
        yield page
    finally:
        await browser.close()


@pytest.fixture
async def async_elementHandle(async_page):
    return await async_page.querySelector('form')


@pytest.mark.asyncio
async def test_pvrt_trackPageAsync__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
       await pvrt.trackPageAsync(None, 'name')


@pytest.mark.asyncio
async def test_pvrt_trackPageAsync__default_options(pvrt, async_page, async_browserType):
    await pvrt.trackPageAsync(async_page, 'image name')

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os is None
    assert testRun.browser == async_browserType.name
    assert testRun.viewport == '1024x768'
    assert testRun.device is None
    assert testRun.diffTollerancePercent is None
    assert testRun.ignoreAreas is None


@pytest.mark.asyncio
async def test_pvrt_trackPageAsync(pvrt, async_page, async_browserType):
    await pvrt.trackPageAsync(
        async_page,
        'image name',
        visual_regression_tracker.playwright.PageTrackOptions(
            diffTollerancePercent=10,
            ignoreAreas=[
                visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
            ],
            screenshotOptions=visual_regression_tracker.playwright.PageScreenshotOptions(
                timeout=1000,
                type='jpeg',
                path=None,
                quality=100,
                omitBackground=False,
                fullPage=True,
            ),
            agent=visual_regression_tracker.playwright.Agent(
                os='os',
                device='device',
                viewport='123x345',
            ),
        ),
    )

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os == 'os'
    assert testRun.browser == async_browserType.name
    assert testRun.viewport == '1024x768'
    assert testRun.device == 'device'
    assert testRun.diffTollerancePercent == 10
    assert testRun.ignoreAreas == [
        visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
    ]


@pytest.mark.asyncio
async def test_pvrt_trackElementHandleAsync__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
        await pvrt.trackElementHandleAsync(None, 'name')


@pytest.mark.asyncio
async def test_pvrt_trackElementHandleAsync__default_options(pvrt, async_elementHandle, async_browserType):
    await pvrt.trackElementHandleAsync(async_elementHandle, 'image name')

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os is None
    assert testRun.browser == async_browserType.name
    assert testRun.viewport is None
    assert testRun.device is None
    assert testRun.diffTollerancePercent is None
    assert testRun.ignoreAreas is None


@pytest.mark.asyncio
async def test_pvrt_trackElementHandleAsync(pvrt, async_elementHandle, async_browserType):
    await pvrt.trackElementHandleAsync(
        async_elementHandle,
        'image name',
        visual_regression_tracker.playwright.ElementHandleTrackOptions(
            diffTollerancePercent=10,
            ignoreAreas=[
                visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
            ],
            screenshotOptions=visual_regression_tracker.playwright.ElementHandleScreenshotOptions(
                timeout=1000,
                type='jpeg',
                path=None,
                quality=100,
                omitBackground=False,
            ),
            agent=visual_regression_tracker.playwright.Agent(
                os='os',
                device='device',
                viewport='123x345',
            ),
        ),
    )

    pvrt.track.assert_called_once()

    testRun = pvrt.track.call_args[0][0]
    assert testRun.name == 'image name'
    assert is_base64(testRun.imageBase64) and len(testRun.imageBase64) > 1024
    assert testRun.os == 'os'
    assert testRun.browser == async_browserType.name
    assert testRun.viewport == '123x345'
    assert testRun.device == 'device'
    assert testRun.diffTollerancePercent == 10
    assert testRun.ignoreAreas == [
        visual_regression_tracker.types.IgnoreArea(1, 2, 3, 4),
    ]



def is_base64(val):
    try:
        assert isinstance(val, str)
        base64.b64decode(val)
        return True
    except binascii.Error:
        return False
