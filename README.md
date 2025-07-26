# vidtoolz-slideshow

[![PyPI](https://img.shields.io/pypi/v/vidtoolz-slideshow.svg)](https://pypi.org/project/vidtoolz-slideshow/)
[![Changelog](https://img.shields.io/github/v/release/sukhbinder/vidtoolz-slideshow?include_prereleases&label=changelog)](https://github.com/sukhbinder/vidtoolz-slideshow/releases)
[![Tests](https://github.com/sukhbinder/vidtoolz-slideshow/workflows/Test/badge.svg)](https://github.com/sukhbinder/vidtoolz-slideshow/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/sukhbinder/vidtoolz-slideshow/blob/main/LICENSE)

Create slideshow with images using ffmpeg

## Installation

First install [vidtoolz](https://github.com/sukhbinder/vidtoolz).

```bash
pip install vidtoolz
```

Then install this plugin in the same environment as your vidtoolz application.

```bash
vidtoolz install vidtoolz-slideshow
```
## Usage

type ``vid slideshow --help`` to get help



## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd vidtoolz-slideshow
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
