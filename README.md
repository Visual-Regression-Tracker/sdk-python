# Python SDK for [Visual Regression Tracker](https://github.com/Visual-Regression-Tracker/Visual-Regression-Tracker)

[![CI](https://github.com/Visual-Regression-Tracker/sdk-python/actions/workflows/workflow.yml/badge.svg)](https://github.com/Visual-Regression-Tracker/sdk-python/actions/workflows/workflow.yml)
[![PyPI](https://img.shields.io/pypi/v/visual-regression-tracker)](https://pypi.org/project/visual-regression-tracker/)

Requires Python 3.11 or later. Use 5.0 or later of this SDK with VRT 6.0; image URLs in results need VRT server 5.0.10 or later.

## Install

```sh
pip install visual-regression-tracker

# or, with the Playwright integration
pip install "visual-regression-tracker[playwright]"
python -m playwright install
```

## Configuration

| Option | Environment variable | Default | Meaning |
|---|---|---|---|
| `apiUrl` | `VRT_APIURL` | `http://localhost:4200` | URL of the VRT API |
| `apiKey` | `VRT_APIKEY` | required | API key of a VRT user |
| `project` | `VRT_PROJECT` | required | Project name or ID |
| `branchName` | `VRT_BRANCHNAME` | required | Current git branch |
| `ciBuildId` | `VRT_CIBUILDID` | none | CI build ID, such as the commit SHA; runs with the same ID share a build |
| `enableSoftAssert` | `VRT_ENABLESOFTASSERT` | `false` | Log a failed check instead of raising `TestRunError` |
| `httpTimeoutInSeconds` | `VRT_HTTPTIMEOUTINSECONDS` | `360` | How long to wait for the server's answer, `0` for no limit. Connecting is limited to 10 s. |

The server compares images while it answers `track()`. With VLM checks or a busy comparison queue that can
take minutes, so keep `httpTimeoutInSeconds` above 300.

A `Config` passed to the constructor is used as it is:

```python
from visual_regression_tracker import VisualRegressionTracker, Config

vrt = VisualRegressionTracker(Config(
    apiUrl='http://localhost:4200',
    apiKey='tXZVHX0EA4YQM1MGDD',
    project='Default project',
    branchName='develop',
    ciBuildId='commit_sha',
))
```

Without one, the SDK reads `vrt.json` from the current working directory, then lets environment variables
override it. `Config.default(path)` reads another file.

```json
{
    "apiUrl": "http://localhost:4200",
    "apiKey": "tXZVHX0EA4YQM1MGDD",
    "project": "Default project",
    "branchName": "develop",
    "ciBuildId": "commit_sha",
    "enableSoftAssert": false,
    "httpTimeoutInSeconds": 360
}
```

```sh
VRT_APIURL="http://localhost:4200" \
VRT_APIKEY="tXZVHX0EA4YQM1MGDD" \
VRT_PROJECT="Default project" \
VRT_BRANCHNAME="develop" \
VRT_CIBUILDID="commit_sha" \
VRT_ENABLESOFTASSERT=true \
VRT_HTTPTIMEOUTINSECONDS=360 \
    python -m pytest
```

Empty variables are ignored. `VRT_ENABLESOFTASSERT` is true for `true` or `1`.

## Usage

```python
from visual_regression_tracker import VisualRegressionTracker, TestRun, IgnoreArea

with VisualRegressionTracker() as vrt:  # start() on enter, stop() on exit
    result = vrt.track(TestRun(
        name='Home page',
        imageBase64=image_base64,
    ))
```

Without the context manager, call `build = vrt.start()` (returns `Build(id, projectId)`) and `vrt.stop()`.

`TestRun` fields:

| Field | Meaning |
|---|---|
| `name` | Required. Name of the image in VRT |
| `imageBase64` | Required. The PNG image, base64 encoded |
| `os`, `browser`, `viewport`, `device` | Optional. Together with `name` they pick the baseline |
| `diffTollerancePercent` | Optional. Allowed difference in %, default 0. The spelling is the API's. |
| `ignoreAreas` | Optional. List of `IgnoreArea(x, y, width, height)` in pixels |

### Playwright

```python
from playwright.sync_api import sync_playwright
from visual_regression_tracker.playwright import PlaywrightVisualRegressionTracker, PageTrackOptions

with sync_playwright() as playwright:
    browser_type = playwright.chromium
    page = browser_type.launch().new_page()
    page.goto('https://www.python.org/')

    with PlaywrightVisualRegressionTracker(browser_type) as vrt:
        vrt.trackPage(page, 'Home page')
        vrt.trackElementHandle(page.query_selector('#touchnav-wrapper'), 'Navigation')
```

`browser` is the Playwright browser name and `viewport` the page's viewport size. The async API has
`trackPageAsync` and `trackElementHandleAsync`.

The last argument is optional: `PageTrackOptions` for `trackPage`, `ElementHandleTrackOptions` for
`trackElementHandle`. Both take:

- `diffTollerancePercent` and `ignoreAreas`, as in `TestRun`;
- `agent: Agent(os, device, viewport)`: baseline fields Playwright doesn't know. `viewport` is used only for
  element handles;
- `screenshotOptions`: arguments for Playwright's `screenshot()`. `PageScreenshotOptions` takes
  `full_page`, `clip`, `omit_background`, `timeout`, `type`, `quality` and `path`.
  `ElementHandleScreenshotOptions` takes the same, without `full_page` and `clip`.

## Result and statuses

`track` and the Playwright methods return a `TestRunResult`:

- `testRunResponse`: `id`, `status`, `url` (the test run in the VRT app), `diffPercent`,
  `diffTollerancePercent`, `pixelMisMatchCount`, `merge`;
- `imageUrl`, `diffUrl` and `baselineUrl`: the images, under `{apiUrl}/images/`. `diffUrl` and
  `baselineUrl` are `None` when there is no diff or baseline.

| `TestRunStatus` | Server status | `track` |
|---|---|---|
| `OK` | `ok` | passes |
| `APPROVED` | `approved` | passes |
| `AUTO_APPROVED` | `autoApproved` | passes |
| `FAILED` | `failed` | passes, as in the other SDKs |
| `NEW` | `new` (no baseline yet) | raises `TestRunError` |
| `UNRESOLVED` | `unresolved` (difference found) | raises `TestRunError` |
| `UNKNOWN` | any other | passes, logs a warning |

With `enableSoftAssert`, `track` logs `new` and `unresolved` as errors instead of raising.

## Errors

All errors derive from `VisualRegressionTrackerError`.

| Error | When |
|---|---|
| `ServerError` | The server answered with an HTTP error. `status_code` and the server's `message`; 413 and 422 add a hint about the server's size limits. |
| `RequestError` | No answer: connection refused, connect timeout, or read timeout after `httpTimeoutInSeconds`. Has the `url`. A read timeout on `track` doesn't mean the server dropped the test run: it may still be stored. |
| `TestRunError` | `track` got `new` or `unresolved`. Has the `status`. |
| `MissingConfigurationError` | A required option is not set. Has the `field`. |
| `InvalidConfigurationError` | An option has an invalid value. Has the `field`. |
| `VisualRegressionTrackerError` | `track` or `stop` before `start`. |

## Development

```sh
pip install -e '.[playwright]' -r requirements.txt
python -m playwright install chromium
python -m pytest
```

`tox` runs the tests on every supported Python.

## Releasing

Merging to `master` releases. [semantic-release](https://semantic-release.gitbook.io/) reads the
[Conventional Commits](https://www.conventionalcommits.org/) since the last tag: `fix:`, `perf:` and `revert:` make a
patch, `feat:` a minor, and `!` after the type (`feat!:`) or a `BREAKING CHANGE:` footer a major release.
Other types (`chore:`, `ci:`, `docs:`, ...) release nothing. A squash merge takes the PR title (or, for a
single-commit PR, that commit's message) as its subject, so keep both conventional.

The `Release` workflow runs the tests, tags the commit (`5.1.0`, no `v`), publishes to PyPI and then
publishes the GitHub release with the generated notes. The package version comes from the tag
(setuptools-scm); nothing is committed back.

If publishing fails, the tag and a draft release already exist: re-run the failed jobs of that run
(not the whole run) before anything else is merged.

## Links

- [Visual Regression Tracker](https://github.com/Visual-Regression-Tracker/Visual-Regression-Tracker): the server and how to run it
- [Python examples](https://github.com/Visual-Regression-Tracker/examples-python)
- [Other SDKs and agents](https://github.com/Visual-Regression-Tracker)
- [Licence: Apache-2.0](LICENSE)
