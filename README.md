# Python SDK for [Visual Regression Tracker](https://github.com/Visual-Regression-Tracker/Visual-Regression-Tracker)

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Visual-Regression-Tracker/sdk-python&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&utm_medium=referral&utm_content=Visual-Regression-Tracker/sdk-python&utm_campaign=Badge_Coverage)

## Install

```python
pip install visual-regression-tracker

# or, with playwright integration
pip install visual-regression-tracker[playwright]
python -m playwright install
```

## Usage

### Import

```python
from visual_regression_tracker import VisualRegressionTracker, Config, TestRun
```

### Configure connection

#### As python
```python
config = Config(
    # apiUrl - URL where backend is running 
    apiUrl='http://localhost:4200',

    # project - Project name or ID
    project='Default project',

    # apiKey - User apiKey
    apiKey='tXZVHX0EA4YQM1MGDD',

    # ciBuildId - Current git commit SHA
    ciBuildId='commit_sha',

    # branch - Current git branch 
    branchName='develop',

    # enableSoftAssert - Log errors instead of exceptions
    enableSoftAssert=False,
)

vrt = VisualRegressionTracker(config)
```

#### Or, as JSON config file `vrt.json`
```json
{
    "apiUrl":"http://localhost:4200",
    "project":"Default project",
    "apiKey":"tXZVHX0EA4YQM1MGDD",
    "ciBuildId":"commit_sha",
    "branchName":"develop",
    "enableSoftAssert":false
}
```
```python
vrt = VisualRegressionTracker()
```

#### Or, as environment variables
```sh
VRT_APIURL="http://localhost:4200" \
VRT_PROJECT="Default project" \
VRT_APIKEY="tXZVHX0EA4YQM1MGDD" \
VRT_CIBUILDID="commit_sha" \
VRT_BRANCHNAME="develop" \
VRT_ENABLESOFTASSERT=true \
    python
```
```python
vrt = VisualRegressionTracker()
```

### Setup / Teardown

As context manager:
```python
with vrt:
    ...
    # track test runs
    ...
```

Without context manager:
```python
vrt.start()
...
# track test runs
...
vrt.stop()
```

### Assert

```python
vrt.track(TestRun(
    # Name to be displayed
    # Required
    name='Image name',

    # Base64 encoded string
    # Required
    imageBase64=image,

    # Allowed mismatch tollerance in %
    # Optional
    # Default: 0%
    diffTollerancePercent=1,

    # Optional
    os='Mac',

    # Optional
    browser='Chrome',

    # Optional
    viewport='800x600',

    # Optional
    device='PC',

    # Array of areas to be ignored
    ignoreAreas=[
        IgnoreArea(
            # X-coordinate relative of left upper corner
            # Required
            x=10,
            # Y-coordinate relative of left upper corner
            # Required
            y=20,
            # Area width in px
            # Required
            width=300,
            # Height width in px
            # Required
            height=400
        )
    ],
))
```

### Integration with Microsoft Playwright

#### Imports
```python
from playwright import sync_playwright
from visual_regression_tracker import Config, TestRun
from visual_regression_tracker.p import PlaywrightVisualRegressionTracker
```

#### Start playwright and navigate to page
```python
playwright = sync_playwright().start()
browserType = playwright.chromium
browser = browserType.launch(headless=False)
page = browser.newPage()
page.goto('https://www.python.org/')
```

#### Configure connection to VRT server
```python
vrt = PlaywrightVisualRegressionTracker(browserType, config)
```

#### Setup / Tear down

As context manager:
```python
with vrt:
    ...
    # track test runs
    ...
```

Without context manager:
```python
vrt.start()
...
# track test runs
...
vrt.stop()
```

#### Track page
```python
vrt.trackPage(page, imageName[, options])
```

- `page: Page` [Playwright page](https://microsoft.github.io/playwright-python/sync_api.html#playwright.sync_api.Page)

- `imageName: str` name for the taken screenshot image

- `options: PageTrackOptions` optional configuration with:
  - `diffTollerancePercent: float` specify acceptable difference from baseline, between `0-100`.

  - `ignoreAreas: List[IgnoreArea]` 
    - `x: int`  X-coordinate relative of left upper corner
    - `y: int`  Y-coordinate relative of left upper corner
    - `width: int`  area width in px
    - `height: int` area height in px

  - `screenshotOptions: PageScreenshotOptions` configuration for Playwrights `screenshot` method
    - `full_page: bool`  When true, takes a screenshot of the full scrollable page, instead of the currently visibvle viewport. Defaults to `false`.

    - `omit_background: bool`  Hides default white background and allows capturing screenshots with transparency. Defaults to `false`.

    - `clip: FloatRect` An object which specifies clipping of the resulting image. Should have the following fields:

      - `x: float` x-coordinate of top-left corner of clip area
      - `y: float` y-coordinate of top-left corner of clip area
      - `width: float` width of clipping area
      - `height: float` height of clipping area

    - `timeout: float` Maximum time in milliseconds, defaults to 30 seconds, pass 0 to disable timeout.

  - `agent: Agent` Additional information to mark baseline across agents that have different:
    - `os: str`  operating system name, like Windows, Mac, etc.
    - `device: str`  device name, PC identifier, mobile identifier etc.
    - `viewport: str` viewport size.

#### Track element handle
```python
vrt.trackElementHandle(elementHandle, imageName[, options])
```

- `elementHandle: ElementHandle` [Playwright ElementHandle](https://microsoft.github.io/playwright-python/sync_api.html#playwright.sync_api.ElementHandle)

- `imageName: str` name for the taken screenshot image

- `options: ElementHandleTrackOptions` optional configuration with:
  - `diffTollerancePercent: float` specify acceptable difference from baseline, between `0-100`.

  - `ignoreAreas: List[IgnoreArea]` 
    - `x: int`  X-coordinate relative of left upper corner
    - `y: int`  Y-coordinate relative of left upper corner
    - `width: int`  area width in px
    - `height: int` area height in px

  - `screenshotOptions: ElementHandleScreenshotOptions` configuration for Playwrights `screenshot` method

    - `omit_background: bool`  Hides default white background and allows capturing screenshots with transparency. Defaults to `false`.

    - `timeout: float` Maximum time in milliseconds, defaults to 30 seconds, pass 0 to disable timeout.

  - `agent: Agent` Additional information to mark baseline across agents that have different:
    - `os: str`  operating system name, like Windows, Mac, etc.
    - `device: str`  device name, PC identifier, mobile identifier etc.
    - `viewport: str` viewport size.
