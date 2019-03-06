<a name="0.9.0"></a>
# [0.9.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.8.1...v0.9.0) (2019-03-06)


### Features

* improve error messages ([8a1ea4e](https://github.com/andreoliwa/flake8-nitpick/commit/8a1ea4e))
* minimum required version on style file ([4090cdc](https://github.com/andreoliwa/flake8-nitpick/commit/4090cdc))
* one style file can include another (also recursively) ([d963a8d](https://github.com/andreoliwa/flake8-nitpick/commit/d963a8d))



<a name="0.8.1"></a>
## [0.8.1](https://github.com/andreoliwa/flake8-nitpick/compare/v0.8.0...v0.8.1) (2019-03-04)


### Bug Fixes

* **setup.cfg:** comma separated values check failing on pre-commit ([27a37b6](https://github.com/andreoliwa/flake8-nitpick/commit/27a37b6))
* **setup.cfg:** comma separated values still failing on pre-commit, only on the first run ([36ea6f0](https://github.com/andreoliwa/flake8-nitpick/commit/36ea6f0))



<a name="0.8.0"></a>
# [0.8.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.7.1...v0.8.0) (2019-03-04)


### Bug Fixes

* keep showing other errors when pyproject.toml doesn't exist ([dc7f02f](https://github.com/andreoliwa/flake8-nitpick/commit/dc7f02f))
* move nitpick config to an exclusive section on the style file ([cd64361](https://github.com/andreoliwa/flake8-nitpick/commit/cd64361))
* use only yield to return values ([af7d8d2](https://github.com/andreoliwa/flake8-nitpick/commit/af7d8d2))
* use yaml.safe_load() ([b1df589](https://github.com/andreoliwa/flake8-nitpick/commit/b1df589))


### Features

* allow configuration of a missing message for each file ([fd053aa](https://github.com/andreoliwa/flake8-nitpick/commit/fd053aa))
* allow multiple style files ([22505ce](https://github.com/andreoliwa/flake8-nitpick/commit/22505ce))
* check root keys on pre-commit file (e.g.: fail_fast) ([9470aed](https://github.com/andreoliwa/flake8-nitpick/commit/9470aed))
* invalidate cache on every run ([e985a0a](https://github.com/andreoliwa/flake8-nitpick/commit/e985a0a))
* suggest initial contents for missing setup.cfg ([8d33b18](https://github.com/andreoliwa/flake8-nitpick/commit/8d33b18))
* suggest installing poetry ([5b6038c](https://github.com/andreoliwa/flake8-nitpick/commit/5b6038c))
* **pre-commit:** suggest pre-commit install ([76b980f](https://github.com/andreoliwa/flake8-nitpick/commit/76b980f))


### Tests

* absent files ([d3ca8c4](https://github.com/andreoliwa/flake8-nitpick/commit/d3ca8c4))


### BREAKING CHANGES

* Comma separated values was moved to a different section in the TOML file:

Before:
["setup.cfg".nitpick]
comma_separated_values = ["food.eat"]

Now:
[nitpick.files."setup.cfg"]
comma_separated_values = ["food.eat"]
* The format of the absent files has changed in the style TOML file.

Before:
[[files.absent]]
file = "remove-this.txt"
message = "This file should be removed because of some reason"
[[files.absent]]
file = "another-useless-file-without-message.cfg"

Now:
[nitpick.files.absent]
"remove-this.txt" = "This file should be removed because of some reason"
"another-useless-file-without-message.cfg" = ""



<a name="0.7.1"></a>
## [0.7.1](https://github.com/andreoliwa/flake8-nitpick/compare/v0.7.0...v0.7.1) (2019-02-14)


### Bug Fixes

* Missing flake8 entry point on pyproject.toml ([a416007](https://github.com/andreoliwa/flake8-nitpick/commit/a416007))



<a name="0.7.0"></a>
# [0.7.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.6.0...v0.7.0) (2019-02-14)


### Features

* Suggest initial contents for missing .pre-commit-config.yaml ([16a6256](https://github.com/andreoliwa/flake8-nitpick/commit/16a6256))



<a name="0.6.0"></a>
# [0.6.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.5.0...v0.6.0) (2019-01-28)


### build

* Ignore .tox dir on flake8 and isort ([462233e](https://github.com/andreoliwa/flake8-nitpick/commit/462233e))
* Update packages ([36bd5ba](https://github.com/andreoliwa/flake8-nitpick/commit/36bd5ba))

### ci

* Add code coverage with Coveralls (#5) ([3995e13](https://github.com/andreoliwa/flake8-nitpick/commit/3995e13))
* Fix Coveralls badge (point to master) ([bae533d](https://github.com/andreoliwa/flake8-nitpick/commit/bae533d))
* Run flake8 and pytest on Travis ([dbb6000](https://github.com/andreoliwa/flake8-nitpick/commit/dbb6000))

### docs

* Add more info to pyproject.toml ([1e0d1a2](https://github.com/andreoliwa/flake8-nitpick/commit/1e0d1a2))

### feat

* Configure comma separated values on the style file ([7ae6622](https://github.com/andreoliwa/flake8-nitpick/commit/7ae6622))
* Suggest poetry init when pyproject.toml does not exist ([366c2b6](https://github.com/andreoliwa/flake8-nitpick/commit/366c2b6))

### fix

* DeprecationWarning: Using or importing the ABCs from 'collections' in ([80f7e24](https://github.com/andreoliwa/flake8-nitpick/commit/80f7e24))

### style

* Ignore build dir on flake8 and isort ([1c18ce3](https://github.com/andreoliwa/flake8-nitpick/commit/1c18ce3))
* Ignore tox dir (flake8), set tests module as first party (isort) ([4fbad20](https://github.com/andreoliwa/flake8-nitpick/commit/4fbad20))

### test

* Comma separated keys on setup.cfg (flake8.ignore) ([b5d8ce7](https://github.com/andreoliwa/flake8-nitpick/commit/b5d8ce7))
* No main Python file on the root dir ([f67f870](https://github.com/andreoliwa/flake8-nitpick/commit/f67f870))
* Test a project with no root dir ([6ccf977](https://github.com/andreoliwa/flake8-nitpick/commit/6ccf977))
* Test most generic functions ([3704c9f](https://github.com/andreoliwa/flake8-nitpick/commit/3704c9f))



<a name="0.5.0"></a>
# [0.5.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.4.0...v0.5.0) (2019-01-09)


### build

* Add flake8-quotes ([7c39870](https://github.com/andreoliwa/flake8-nitpick/commit/7c39870))
* Bump version in pyproject.toml ([eef3d3d](https://github.com/andreoliwa/flake8-nitpick/commit/eef3d3d))
* Create but don't push git tag, it is needed by the changelog ([f60382f](https://github.com/andreoliwa/flake8-nitpick/commit/f60382f))

### feat

* Add .venv to the absent files list ([153a7ca](https://github.com/andreoliwa/flake8-nitpick/commit/153a7ca))
* Add flake8-quotes to the default style ([60b3726](https://github.com/andreoliwa/flake8-nitpick/commit/60b3726))



<a name="0.4.0"></a>
# [0.4.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.3.0...v0.4.0) (2019-01-07)


### feat

* Check files that should not exist (like .isort.cfg) ([1901bb8](https://github.com/andreoliwa/flake8-nitpick/commit/1901bb8))
* Check pre-commit config file and the presence of hooks ([b1333db](https://github.com/andreoliwa/flake8-nitpick/commit/b1333db))
* Warn about replacing requirements.txt by pyproject.toml ([dacb091](https://github.com/andreoliwa/flake8-nitpick/commit/dacb091))

### fix

* Don't break when pyproject.toml or setup.cfg don't exist ([6a546c1](https://github.com/andreoliwa/flake8-nitpick/commit/6a546c1))
* Only check rules if the file exists ([66e42d2](https://github.com/andreoliwa/flake8-nitpick/commit/66e42d2))

### refactor

* Check absence of pipenv files using the .toml config ([4002015](https://github.com/andreoliwa/flake8-nitpick/commit/4002015))
* Remove should_exist_default, consider existence of a config ([8b22926](https://github.com/andreoliwa/flake8-nitpick/commit/8b22926))
* Use a mixin with a base error number for each class ([bb7e73d](https://github.com/andreoliwa/flake8-nitpick/commit/bb7e73d))



<a name="0.3.0"></a>
# [0.3.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.2.0...v0.3.0) (2019-01-03)


### feat

* Show different key/value pairs on pyproject.toml, case insensitive boolean values ([30e03eb](https://github.com/andreoliwa/flake8-nitpick/commit/30e03eb))

### fix

* KeyError when section does not exist on setup.cfg ([e652604](https://github.com/andreoliwa/flake8-nitpick/commit/e652604))



<a name="0.2.0"></a>
# [0.2.0](https://github.com/andreoliwa/flake8-nitpick/compare/v0.1.1...v0.2.0) (2018-12-23)


### build

* Upgrade packages and lint with flake8 ([22f4c62](https://github.com/andreoliwa/flake8-nitpick/commit/22f4c62))
* v0.2.0 (with conventional-changelog and bumpversion) ([bc8a8a8](https://github.com/andreoliwa/flake8-nitpick/commit/bc8a8a8))

### docs

* Add docs on how to configure pyproject.toml and style ([4a1d221](https://github.com/andreoliwa/flake8-nitpick/commit/4a1d221))

### feat

* Check missing key/value pairs in pyproject.toml ([190aa6c](https://github.com/andreoliwa/flake8-nitpick/commit/190aa6c))
* Compare setup.cfg configuration ([2bf144a](https://github.com/andreoliwa/flake8-nitpick/commit/2bf144a))
* First warning, only on the main Python file ([0b30506](https://github.com/andreoliwa/flake8-nitpick/commit/0b30506))
* Read config from pyproject.toml, cache data, run only on one Python  ([265daa5](https://github.com/andreoliwa/flake8-nitpick/commit/265daa5))
* Read style from TOML file/URL (or climb directory tree) ([84f19d6](https://github.com/andreoliwa/flake8-nitpick/commit/84f19d6))
* Respect the files section on nitpick.toml ([9e36a02](https://github.com/andreoliwa/flake8-nitpick/commit/9e36a02))
* Use nitpick's own default style file if none is provided ([4701b86](https://github.com/andreoliwa/flake8-nitpick/commit/4701b86))

### refactor

* Rename to flake8-nitpick ([1e4f42e](https://github.com/andreoliwa/flake8-nitpick/commit/1e4f42e))

### test

* Setup logging ([5472518](https://github.com/andreoliwa/flake8-nitpick/commit/5472518))



<a name="0.1.1"></a>
## [0.1.1](https://github.com/andreoliwa/flake8-nitpick/compare/v0.1.0...v0.1.1) (2018-03-23)

README badges.

<a name="0.1.0"></a>
# 0.1.0 (2018-03-23)

First release.
