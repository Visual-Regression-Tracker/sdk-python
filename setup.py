from setuptools import setup

setup(
    name='visual_regression_tracker',
    version='0.1',
    description='Open source, self hosted solution for visual testing '
                'and managing results of visual testing.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='',
    license='APACHE',
    url='https://github.com/Visual-Regression-Tracker/'
        'Visual-Regression-Tracker',
    packages=['visual_regression_tracker'],
    requires=['requests']
)
