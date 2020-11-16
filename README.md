# Python SDK for [Visual Regression Tracker](https://github.com/Visual-Regression-Tracker/Visual-Regression-Tracker)

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Visual-Regression-Tracker/sdk-python&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/0b98190cea064d6f9f1210da653ba37b)](https://www.codacy.com/gh/Visual-Regression-Tracker/sdk-python?utm_source=github.com&utm_medium=referral&utm_content=Visual-Regression-Tracker/sdk-python&utm_campaign=Badge_Coverage)

## Install

```python
pip install visual_regression_tracker
```

## Usage

### Import

```python
from visual_regression_tracker import VisualRegressionTracker, Config, TestRun
```

### Configure connection

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