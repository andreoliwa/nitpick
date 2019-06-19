# [0.16.0](https://github.com/andreoliwa/nitpick/compare/v0.15.0...v0.16.0) (2019-06-19)


### Features

* **pre-commit:** add nitpick hooks to use on .pre-commit-config.yaml ([92c13ae](https://github.com/andreoliwa/nitpick/commit/92c13ae))

# [0.15.0](https://github.com/andreoliwa/nitpick/compare/v0.14.0...v0.15.0) (2019-06-17)


### Features

* merge all styles into a single TOML file on the cache dir ([d803f64](https://github.com/andreoliwa/nitpick/commit/d803f64))
* **pre-commit:** compare missing and different keys on hooks ([#57](https://github.com/andreoliwa/nitpick/issues/57)) ([a8e2958](https://github.com/andreoliwa/nitpick/commit/a8e2958))

# [0.14.0](https://github.com/andreoliwa/nitpick/compare/v0.13.1...v0.14.0) (2019-06-07)


### Features

* rename project from "flake8-nitpick" to "nitpick" ([75be3b8](https://github.com/andreoliwa/nitpick/commit/75be3b8))

## [0.13.1](https://github.com/andreoliwa/nitpick/compare/v0.13.0...v0.13.1) (2019-06-07)


### Bug Fixes

* show warning about project being renamed to "nitpick" ([fda30fd](https://github.com/andreoliwa/nitpick/commit/fda30fd))

# [0.13.0](https://github.com/andreoliwa/nitpick/compare/v0.12.0...v0.13.0) (2019-06-06)


### Features

* run on Python 3.5 ([185e121](https://github.com/andreoliwa/nitpick/commit/185e121))

# [0.12.0](https://github.com/andreoliwa/nitpick/compare/v0.11.0...v0.12.0) (2019-06-03)


### Features

* get default style file from current version, not from master ([e0dccb8](https://github.com/andreoliwa/nitpick/commit/e0dccb8))

# [0.11.0](https://github.com/andreoliwa/nitpick/compare/v0.10.3...v0.11.0) (2019-03-31)


### Features

* allow pyproject.toml to be located in root dir's parents (thanks [@michael-k](https://github.com/michael-k)) ([#21](https://github.com/andreoliwa/nitpick/issues/21)) ([d3c4d74](https://github.com/andreoliwa/nitpick/commit/d3c4d74))

<a name="0.10.3"></a>
## [0.10.3](https://github.com/andreoliwa/nitpick/compare/v0.10.2...v0.10.3) (2019-03-13)


### Bug Fixes

* ignore FileNotFoundError when removing cache dir ([837bddf](https://github.com/andreoliwa/nitpick/commit/837bddf))



<a name="0.10.2"></a>
## [0.10.2](https://github.com/andreoliwa/nitpick/compare/v0.10.1...v0.10.2) (2019-03-13)


### Bug Fixes

* don't remove cache dir if it doesn't exist (FileNotFoundError) ([d5b6ec9](https://github.com/andreoliwa/nitpick/commit/d5b6ec9))



<a name="0.10.1"></a>
## [0.10.1](https://github.com/andreoliwa/nitpick/compare/v0.10.0...v0.10.1) (2019-03-11)


### Bug Fixes

* fetch private GitHub URLs with a token on the query string ([4cfc118](https://github.com/andreoliwa/nitpick/commit/4cfc118))



<a name="0.10.0"></a>
# [0.10.0](https://github.com/andreoliwa/nitpick/compare/v0.9.0...v0.10.0) (2019-03-11)


### Features

* assume style has a .toml extension when it's missing ([5a584ac](https://github.com/andreoliwa/nitpick/commit/5a584ac))
* read local style files from relative and other root dirs ([82d3675](https://github.com/andreoliwa/nitpick/commit/82d3675))
* read relative styles in subdirectories of a symlink dir ([55634e1](https://github.com/andreoliwa/nitpick/commit/55634e1))
* read styles from relative paths on URLs ([46d1b84](https://github.com/andreoliwa/nitpick/commit/46d1b84))



<a name="0.9.0"></a>
# [0.9.0](https://github.com/andreoliwa/nitpick/compare/v0.8.1...v0.9.0) (2019-03-06)


### Features

* improve error messages ([8a1ea4e](https://github.com/andreoliwa/nitpick/commit/8a1ea4e))
* minimum required version on style file ([4090cdc](https://github.com/andreoliwa/nitpick/commit/4090cdc))
* one style file can include another (also recursively) ([d963a8d](https://github.com/andreoliwa/nitpick/commit/d963a8d))



<a name="0.8.1"></a>
## [0.8.1](https://github.com/andreoliwa/nitpick/compare/v0.8.0...v0.8.1) (2019-03-04)


### Bug Fixes

* **setup.cfg:** comma separated values check failing on pre-commit ([27a37b6](https://github.com/andreoliwa/nitpick/commit/27a37b6))
* **setup.cfg:** comma separated values still failing on pre-commit, only on the first run ([36ea6f0](https://github.com/andreoliwa/nitpick/commit/36ea6f0))



<a name="0.8.0"></a>
# [0.8.0](https://github.com/andreoliwa/nitpick/compare/v0.7.1...v0.8.0) (2019-03-04)


### Bug Fixes

* keep showing other errors when pyproject.toml doesn't exist ([dc7f02f](https://github.com/andreoliwa/nitpick/commit/dc7f02f))
* move nitpick config to an exclusive section on the style file ([cd64361](https://github.com/andreoliwa/nitpick/commit/cd64361))
* use only yield to return values ([af7d8d2](https://github.com/andreoliwa/nitpick/commit/af7d8d2))
* use yaml.safe_load() ([b1df589](https://github.com/andreoliwa/nitpick/commit/b1df589))


### Features

* allow configuration of a missing message for each file ([fd053aa](https://github.com/andreoliwa/nitpick/commit/fd053aa))
* allow multiple style files ([22505ce](https://github.com/andreoliwa/nitpick/commit/22505ce))
* check root keys on pre-commit file (e.g.: fail_fast) ([9470aed](https://github.com/andreoliwa/nitpick/commit/9470aed))
* invalidate cache on every run ([e985a0a](https://github.com/andreoliwa/nitpick/commit/e985a0a))
* suggest initial contents for missing setup.cfg ([8d33b18](https://github.com/andreoliwa/nitpick/commit/8d33b18))
* suggest installing poetry ([5b6038c](https://github.com/andreoliwa/nitpick/commit/5b6038c))
* **pre-commit:** suggest pre-commit install ([76b980f](https://github.com/andreoliwa/nitpick/commit/76b980f))


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
## [0.7.1](https://github.com/andreoliwa/nitpick/compare/v0.7.0...v0.7.1) (2019-02-14)


### Bug Fixes

* Missing flake8 entry point on pyproject.toml ([a416007](https://github.com/andreoliwa/nitpick/commit/a416007))



<a name="0.7.0"></a>
# [0.7.0](https://github.com/andreoliwa/nitpick/compare/v0.6.0...v0.7.0) (2019-02-14)


### Features

* Suggest initial contents for missing .pre-commit-config.yaml ([16a6256](https://github.com/andreoliwa/nitpick/commit/16a6256))



<a name="0.6.0"></a>
# [0.6.0](https://github.com/andreoliwa/nitpick/compare/v0.5.0...v0.6.0) (2019-01-28)


### Features

* Configure comma separated values on the style file ([7ae6622](https://github.com/andreoliwa/nitpick/commit/7ae6622))
* Suggest poetry init when pyproject.toml does not exist ([366c2b6](https://github.com/andreoliwa/nitpick/commit/366c2b6))

### Bug Fixes

* DeprecationWarning: Using or importing the ABCs from 'collections' in ([80f7e24](https://github.com/andreoliwa/nitpick/commit/80f7e24))



<a name="0.5.0"></a>
# [0.5.0](https://github.com/andreoliwa/nitpick/compare/v0.4.0...v0.5.0) (2019-01-09)


### Features

* Add .venv to the absent files list ([153a7ca](https://github.com/andreoliwa/nitpick/commit/153a7ca))
* Add flake8-quotes to the default style ([60b3726](https://github.com/andreoliwa/nitpick/commit/60b3726))



<a name="0.4.0"></a>
# [0.4.0](https://github.com/andreoliwa/nitpick/compare/v0.3.0...v0.4.0) (2019-01-07)


### Features

* Check files that should not exist (like .isort.cfg) ([1901bb8](https://github.com/andreoliwa/nitpick/commit/1901bb8))
* Check pre-commit config file and the presence of hooks ([b1333db](https://github.com/andreoliwa/nitpick/commit/b1333db))
* Warn about replacing requirements.txt by pyproject.toml ([dacb091](https://github.com/andreoliwa/nitpick/commit/dacb091))

### Bug Fixes

* Don't break when pyproject.toml or setup.cfg don't exist ([6a546c1](https://github.com/andreoliwa/nitpick/commit/6a546c1))
* Only check rules if the file exists ([66e42d2](https://github.com/andreoliwa/nitpick/commit/66e42d2))



<a name="0.3.0"></a>
# [0.3.0](https://github.com/andreoliwa/nitpick/compare/v0.2.0...v0.3.0) (2019-01-03)


### Features

* Show different key/value pairs on pyproject.toml, case insensitive boolean values ([30e03eb](https://github.com/andreoliwa/nitpick/commit/30e03eb))

### Bug Fixes

* KeyError when section does not exist on setup.cfg ([e652604](https://github.com/andreoliwa/nitpick/commit/e652604))



<a name="0.2.0"></a>
# [0.2.0](https://github.com/andreoliwa/nitpick/compare/v0.1.1...v0.2.0) (2018-12-23)


### Features

* Check missing key/value pairs in pyproject.toml ([190aa6c](https://github.com/andreoliwa/nitpick/commit/190aa6c))
* Compare setup.cfg configuration ([2bf144a](https://github.com/andreoliwa/nitpick/commit/2bf144a))
* First warning, only on the main Python file ([0b30506](https://github.com/andreoliwa/nitpick/commit/0b30506))
* Read config from pyproject.toml, cache data, run only on one Python  ([265daa5](https://github.com/andreoliwa/nitpick/commit/265daa5))
* Read style from TOML file/URL (or climb directory tree) ([84f19d6](https://github.com/andreoliwa/nitpick/commit/84f19d6))
* Respect the files section on nitpick.toml ([9e36a02](https://github.com/andreoliwa/nitpick/commit/9e36a02))
* Use nitpick's own default style file if none is provided ([4701b86](https://github.com/andreoliwa/nitpick/commit/4701b86))



<a name="0.1.1"></a>
## [0.1.1](https://github.com/andreoliwa/nitpick/compare/v0.1.0...v0.1.1) (2018-03-23)

README badges.

<a name="0.1.0"></a>
## 0.1.0 (2018-03-23)

First release.
