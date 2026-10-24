import base64
import binascii
import pytest
import pytest_asyncio
import visual_regression_tracker
playwright = pytest.importorskip('playwright')
import visual_regression_tracker.playwright

CONFIG = visual_regression_tracker.Config(
    apiUrl='https://server/',
    ciBuildId='CI Build Id',
    branchName='Branch Name',
    project='Project',
    apiKey='API Key',
    enableSoftAssert=False,
)


@pytest.fixture
def pvrt(async_browserType, mocker):
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'start')
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'track')
    mocker.patch.object(visual_regression_tracker.VisualRegressionTracker, 'stop')
    pvrt = visual_regression_tracker.playwright.PlaywrightVisualRegressionTracker(async_browserType, CONFIG)
    return pvrt


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def async_playwright():
    async with playwright.async_api.async_playwright() as p:
        yield p


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def async_browserType(async_playwright):
    return async_playwright.chromium


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def async_page(async_browserType):
    browser = await async_browserType.launch(headless=True)
    try:
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1024, "height": 768})
        await page.goto('https://google.com')
        yield page
    finally:
        await browser.close()


@pytest_asyncio.fixture(loop_scope='session')
async def async_elementHandle(async_page):
    return await async_page.query_selector('form')


@pytest.mark.asyncio(loop_scope='session')
async def test_pvrt_trackPageAsync__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
        await pvrt.trackPageAsync(None, 'name')


@pytest.mark.asyncio(loop_scope='session')
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


@pytest.mark.asyncio(loop_scope='session')
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
                omit_background=False,
                full_page=True,
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


@pytest.mark.asyncio(loop_scope='session')
async def test_pvrt_trackElementHandleAsync__throws_if_no_page(pvrt):
    with pytest.raises(Exception):
        await pvrt.trackElementHandleAsync(None, 'name')


@pytest.mark.asyncio(loop_scope='session')
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


@pytest.mark.asyncio(loop_scope='session')
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
                omit_background=False,
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
