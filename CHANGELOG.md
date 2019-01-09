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
