# Python SDK for [Visual Regression Tracker](https://github.com/Visual-Regression-Tracker/Visual-Regression-Tracker)

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Visual-Regression-Tracker/sdk-python&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&utm_medium=referral&utm_content=Visual-Regression-Tracker/sdk-python&utm_campaign=Badge_Coverage)

Requires Python 3.10 or later. Image URLs in results need VRT server 5.0.10 or later; use 5.x of this SDK with VRT 6.0.

## Install

```sh
pip install visual-regression-tracker

# or, with playwright integration
pip install "visual-regression-tracker[playwright]"
python -m playwright install
```

## Usage

### Import

```python
from visual_regression_tracker import VisualRegressionTracker, Config, TestRun, IgnoreArea
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

    # httpTimeoutInSeconds - How long to wait for the server's answer, 0 for no limit.
    # The server compares images while answering track(); with VLM checks or a busy
    # comparison queue that can take minutes, so keep it above 300.
    httpTimeoutInSeconds=360,
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
    "enableSoftAssert":false,
    "httpTimeoutInSeconds":360
}
```

`vrt.json` is read from the current working directory.
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
VRT_HTTPTIMEOUTINSECONDS=360 \
    python
```
Empty variables are ignored.
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
build = vrt.start()  # Build(id, projectId)
...
# track test runs
...
vrt.stop()
```

### Assert

```python
result = vrt.track(TestRun(
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

`track` returns a `TestRunResult`: `testRunResponse` (with `status` and the `url` of the test run in the
VRT app) and `imageUrl`, `diffUrl`, `baselineUrl`.

`track` raises `TestRunError` when the status is `new` (no baseline yet) or `unresolved` (difference found);
with `enableSoftAssert` it logs the error instead. `ok`, `approved` and `autoApproved` pass; `failed` passes
too, as in the JavaScript SDK. A status this SDK does not know becomes `TestRunStatus.UNKNOWN`.

An HTTP error from the server raises `ServerError` with `status_code` and the server's `message`.
A request that gets no answer (connection refused, connect timeout after 10 s, read timeout after
`httpTimeoutInSeconds`) raises `RequestError` with the `url`. A read timeout on `track` does not mean
the server dropped the test run: it may still be stored.

### Integration with Microsoft Playwright

#### Imports
```python
from playwright.sync_api import sync_playwright
from visual_regression_tracker import Config
from visual_regression_tracker.playwright import PlaywrightVisualRegressionTracker
```

#### Start playwright and navigate to page
```python
playwright = sync_playwright().start()
browserType = playwright.chromium
browser = browserType.launch(headless=False)
page = browser.new_page()
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
result = vrt.trackPage(page, imageName[, options])
```

- `page: Page` [Playwright page](https://playwright.dev/python/docs/api/class-page)

- `imageName: str` name for the taken screenshot image

- `options: PageTrackOptions` optional configuration with:
  - `diffTollerancePercent: float` specify acceptable difference from baseline, between `0-100`.

  - `ignoreAreas: List[IgnoreArea]` 
    - `x: int`  X-coordinate relative of left upper corner
    - `y: int`  Y-coordinate relative of left upper corner
    - `width: int`  area width in px
    - `height: int` area height in px

  - `screenshotOptions: PageScreenshotOptions` configuration for Playwrights `screenshot` method
    - `full_page: bool`  When true, takes a screenshot of the full scrollable page, instead of the currently visible viewport. Defaults to `false`.

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
result = vrt.trackElementHandle(elementHandle, imageName[, options])
```

The async API has `trackPageAsync` and `trackElementHandleAsync`. All four return the same `TestRunResult` as `track`.

- `elementHandle: ElementHandle` [Playwright ElementHandle](https://playwright.dev/python/docs/api/class-elementhandle)

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

## Development

```sh
pip install -e '.[playwright]' -r requirements.txt
python -m playwright install chromium
python -m pytest
```

## Releasing

Merging to `master` releases. [semantic-release](https://semantic-release.gitbook.io/) reads the
[Conventional Commits](https://www.conventionalcommits.org/) since the last tag: `fix:` makes a patch,
`feat:` a minor, and `!` after the type (`feat!:`) or a `BREAKING CHANGE:` footer a major release.
Other types (`chore:`, `ci:`, `docs:`, ...) release nothing. With squash merging, the PR title is the
commit message, so give the PR a conventional title.

The `Release` workflow runs the tests, tags the commit (`5.1.0`, no `v`), publishes to PyPI and then
publishes the GitHub release with the generated notes. The package version comes from the tag
(setuptools-scm); nothing is committed back.
