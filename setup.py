from setuptools import setup

setup(
    name='visual_regression_tracker',
    version='4.9.0',
    description='Open source, self hosted solution for visual testing '
                'and managing results of visual testing.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='',
    license='APACHE',
    url='https://github.com/Visual-Regression-Tracker/'
        'Visual-Regression-Tracker',
    packages=['visual_regression_tracker'],
    python_requires='>=3.6',
    install_requires=['requests', 'dacite', 'dataclasses;python_version<"3.7"'],
    extras_require={
        # Playwright provides browser automation, requires python3.7 and above.
        "playwright": [
            "playwright",
        ],
    },
)
