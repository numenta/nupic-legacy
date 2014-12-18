# Changelog

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
