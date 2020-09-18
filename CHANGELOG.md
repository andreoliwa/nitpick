# [0.23.0](https://github.com/andreoliwa/nitpick/compare/v0.22.2...v0.23.0) (2020-09-18)


### Bug Fixes

* get uiri/toml@9be6458 to fix conflict with black@20.8b1 ([fd2a44a](https://github.com/andreoliwa/nitpick/commit/fd2a44aedf253b0b73acec82b4c86b3fe3cc343f)), closes [#200](https://github.com/andreoliwa/nitpick/issues/200)


### Features

* check if a text file contains lines ([#182](https://github.com/andreoliwa/nitpick/issues/182)) ([3173bf7](https://github.com/andreoliwa/nitpick/commit/3173bf7380ef7b4e8221060cb575d606f6f4af2c))
* detect JSON files by extension, no need to declare them first ([6f54480](https://github.com/andreoliwa/nitpick/commit/6f544807867acc1b9234721000bf4c73838b5e72))
* use a plugin system (experimental) ([#180](https://github.com/andreoliwa/nitpick/issues/180)) ([6d2df4f](https://github.com/andreoliwa/nitpick/commit/6d2df4ffd156d9585c6a29bc7498a89e9b59ce16))

## [0.22.2](https://github.com/andreoliwa/nitpick/compare/v0.22.1...v0.22.2) (2020-05-15)


### Bug Fixes

* toml 0.10.1 is now raising ValueError: Circular reference ([ed1174f](https://github.com/andreoliwa/nitpick/commit/ed1174fcf27c82bb10ae0e45427ce6e284e62931)), closes [#159](https://github.com/andreoliwa/nitpick/issues/159)
* **json:** warn about different values ([4f9a891](https://github.com/andreoliwa/nitpick/commit/4f9a891f21d53a40b62f078b8dbd67076a144c5b)), closes [#155](https://github.com/andreoliwa/nitpick/issues/155)

## [0.22.1](https://github.com/andreoliwa/nitpick/compare/v0.22.0...v0.22.1) (2020-03-26)


### Bug Fixes

* broken build that didn't upload v0.22.0 to PyPI ([aaf2f06](https://github.com/andreoliwa/nitpick/commit/aaf2f06c7c563bd1388ebeb03a575b52461c6625))

# [0.22.0](https://github.com/andreoliwa/nitpick/compare/v0.21.4...v0.22.0) (2020-03-26)


### Bug Fixes

* consider any Python file (thanks [@tolusonaike](https://github.com/tolusonaike)) ([55c0965](https://github.com/andreoliwa/nitpick/commit/55c096529d40a95f53b13abf04a5b6aaabec0ed9)), closes [#138](https://github.com/andreoliwa/nitpick/issues/138)
* remove setup.py (thanks [@sobolevn](https://github.com/sobolevn) and [@bibz](https://github.com/bibz)) ([5d03744](https://github.com/andreoliwa/nitpick/commit/5d03744d1427997165dd4f11f8f68e0bef0a9083))


### Features

* add flag for offline mode ([#129](https://github.com/andreoliwa/nitpick/issues/129)) ([3650575](https://github.com/andreoliwa/nitpick/commit/36505753e245a065cffc683fc92b4391e72b3627))

## [0.21.4](https://github.com/andreoliwa/nitpick/compare/v0.21.3...v0.21.4) (2020-03-10)


### Bug Fixes

* display the current revision of the hook ([ee09be0](https://github.com/andreoliwa/nitpick/commit/ee09be0731654f72dbbf3d9dd316f476ae24c4cb))

## [0.21.3](https://github.com/andreoliwa/nitpick/compare/v0.21.2...v0.21.3) (2019-12-08)


### Bug Fixes

* concatenate URL manually instead of using Path ([5491b39](https://github.com/andreoliwa/nitpick/commit/5491b396e38aa8851bc7b01f4ecce583ef43655f)), closes [#115](https://github.com/andreoliwa/nitpick/issues/115)

## [0.21.2](https://github.com/andreoliwa/nitpick/compare/v0.21.1...v0.21.2) (2019-10-31)


### Bug Fixes

* infinite loop when climbing directories on Windows ([9915c74](https://github.com/andreoliwa/nitpick/commit/9915c74d52ab10d34b88733abb12958779e00ba8)), closes [#108](https://github.com/andreoliwa/nitpick/issues/108)

## [0.21.1](https://github.com/andreoliwa/nitpick/compare/v0.21.0...v0.21.1) (2019-09-23)


### Bug Fixes

* only check files if they have configured styles ([2cac863](https://github.com/andreoliwa/nitpick/commit/2cac863))

# [0.21.0](https://github.com/andreoliwa/nitpick/compare/v0.20.0...v0.21.0) (2019-08-26)


### Bug Fixes

* use green color to be compatible with click 6.7 ([54a6f4e](https://github.com/andreoliwa/nitpick/commit/54a6f4e)), closes [#81](https://github.com/andreoliwa/nitpick/issues/81)
* **json:** show original JSON key suggestion, without flattening ([d01cd05](https://github.com/andreoliwa/nitpick/commit/d01cd05))


### Features

* **style:** validate the [nitpick.files] section ([96c1c31](https://github.com/andreoliwa/nitpick/commit/96c1c31))
* show help with the documentation URL on validation errors ([83a8f89](https://github.com/andreoliwa/nitpick/commit/83a8f89))
* validate [nitpick.files.present] and [nitpick.files.absent] ([ab068b5](https://github.com/andreoliwa/nitpick/commit/ab068b5))
* validate configuration of JSON files ([e1192a4](https://github.com/andreoliwa/nitpick/commit/e1192a4))

# [0.20.0](https://github.com/andreoliwa/nitpick/compare/v0.19.0...v0.20.0) (2019-08-13)


### Bug Fixes

* report errors on line 0 instead of 1 ([31b13ea](https://github.com/andreoliwa/nitpick/commit/31b13ea)), closes [#73](https://github.com/andreoliwa/nitpick/issues/73)


### Features

* add config to check files that should be present ([408440f](https://github.com/andreoliwa/nitpick/commit/408440f)), closes [#74](https://github.com/andreoliwa/nitpick/issues/74)

# [0.19.0](https://github.com/andreoliwa/nitpick/compare/v0.18.0...v0.19.0) (2019-08-13)


### Bug Fixes

* emit warning when TOML is invalid in a style file (closes [#68](https://github.com/andreoliwa/nitpick/issues/68)) ([b48e0a4](https://github.com/andreoliwa/nitpick/commit/b48e0a4))
* files should not be deleted unless explicitly set in the style ([b5953ff](https://github.com/andreoliwa/nitpick/commit/b5953ff)), closes [#71](https://github.com/andreoliwa/nitpick/issues/71)
* improve the way to find the root dir of the project ([fa3460a](https://github.com/andreoliwa/nitpick/commit/fa3460a)), closes [#72](https://github.com/andreoliwa/nitpick/issues/72)


### Features

* validate the merged style file schema ([1e31d0a](https://github.com/andreoliwa/nitpick/commit/1e31d0a)), closes [#69](https://github.com/andreoliwa/nitpick/issues/69)

# [0.18.0](https://github.com/andreoliwa/nitpick/compare/v0.17.0...v0.18.0) (2019-08-09)


### Bug Fixes

* broken link on README (fixes [#70](https://github.com/andreoliwa/nitpick/issues/70), thanks [@sobolevn](https://github.com/sobolevn)) ([b35bbdb](https://github.com/andreoliwa/nitpick/commit/b35bbdb))


### Features

* **pyproject.toml:** validate [tool.nitpick] section ([765562a](https://github.com/andreoliwa/nitpick/commit/765562a))

# [0.17.0](https://github.com/andreoliwa/nitpick/compare/v0.16.1...v0.17.0) (2019-08-08)


### Bug Fixes

* **setup.cfg:** silently ignore invalid sections to avoid exceptions ([79cb441](https://github.com/andreoliwa/nitpick/commit/79cb441)), closes [#69](https://github.com/andreoliwa/nitpick/issues/69)


### Features

* highlight suggested changes with color ([f49f456](https://github.com/andreoliwa/nitpick/commit/f49f456))
* **json:** check if a JSON file contains the specified JSON data ([47fa133](https://github.com/andreoliwa/nitpick/commit/47fa133))
* **json:** check if a JSON file contains the specified keys ([0f8a53c](https://github.com/andreoliwa/nitpick/commit/0f8a53c))
* **json:** suggest content when file doesn't exist ([502eb3d](https://github.com/andreoliwa/nitpick/commit/502eb3d))
* **pre-commit:** add commitlint hook to the default recommended style ([61f467c](https://github.com/andreoliwa/nitpick/commit/61f467c))

## [0.16.1](https://github.com/andreoliwa/nitpick/compare/v0.16.0...v0.16.1) (2019-06-19)


### Bug Fixes

* don't try to remove the .cache root dir, it leads to errors sometimes ([856d8e7](https://github.com/andreoliwa/nitpick/commit/856d8e7))
* move flake8 plugins from nitpick to pre-commit ([7913e19](https://github.com/andreoliwa/nitpick/commit/7913e19))

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
