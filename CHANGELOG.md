# Changelog

## 0.0.13-dev

## 0.0.12

* Installing python wheel manually.

## 0.0.11

* Fixed bug in release condition.

## 0.0.10

* Trying a custom deployment configuration for better control of pypi deployment files.

## 0.0.9

* Fixed missing `__version__` number problem.
* Distributing `*.i` files from `nupic.bindings` in binary packages.

## 0.0.8

* Updated pypi development status to "Stable", otherwise pypi rejects it.

## 0.0.7

* Updates test entry points to pure python. README instructions for running tests were updated.
* Missing configuration files are no longer ignored. A runtime exception is raised immediately when an expected configuration file is not found. 

## 0.0.6

* Updated pypi encrypted password because of authenitcation failure.
* Only installing wheel on iterative builds, because Travis-CI automatically installs it if "bdist_wheel" is specified in deploy provider directive.

## 0.0.5

* Installing doxygen before doc-build for pypi.

## 0.0.4

* Temporarily removing pycapnp dependency to help current release situation.

## 0.0.3

* Updated deployment logic to account for both deployment scenarios (iterative and release).

## 0.0.2

* Configured pypi deployment on all branches with tags.

## 0.0.1

* Added pypi deployment configuration for binary releases.
* Parsing python requirements in setuptools so they are included within published packages (working toward releases).
* Setting up python wheels packaging and upload to S3 for future distribution.
* Implement logic for reusing segments, to enforce a fixed-size connectivity (nupic.core).
* Added CHANGELOG.md to track changes for versions.
* Added version.txt file to root, read by setuptools to establish version.
