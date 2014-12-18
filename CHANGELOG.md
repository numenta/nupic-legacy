# Changelog

## 0.0.1 (in progress): Pre-pre release, mostly deployment testing

* Added pypi deployment configuration for binary releases.
* Parsing python requirements in setuptools so they are included within published packages (working toward releases).
* Setting up python wheels packaging and upload to S3 for future distribution.
* Implement logic for reusing segments, to enforce a fixed-size connectivity (nupic.core).
* Added CHANGELOG.md to track changes for versions.
* Added version.txt file to root, read by setuptools to establish version.
