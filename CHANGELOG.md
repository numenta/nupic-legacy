# Changelog

## 0.0.34

* Publishing select artifacts to pypi on release.
* Adding empty __init__.py to swarming resource dir so it get's included in linux wheels.

## 0.0.33

* Changed dev version pattern to match what python wants.
* Cleaned up setup and manifest for proper sdists.

## 0.0.32

* Faking extensions to get platform-specific wheels.

## 0.0.31

* Manual wheel filename change for linux upload to pypi.

## 0.0.30

* Creating platform dependent linux wheel file for pypi upload.

## 0.0.29

* Updated OS X wheel filename for pypi.

## 0.0.28

* Only release on tags.

## 0.0.27

* Adding back test runs.

## 0.0.26

* Split release logic into osx/linux scripts
* Adds core capnp files to bindings.
* Remove HtmTest and call it from nupic.core binaries
* GCE now encodes altitude using a 3D coordinate system.

## 0.0.25

* Removing OS X release and using Linux GCC release only.

## 0.0.24

* Trying pip install w/o sudo

## 0.0.23

* Manually upgrading setuptools before pip upgrade before release

## 0.0.22

* Manually upgrading pip on OS X.

## 0.0.21

* Trying release w/o pip, setuptools update

## 0.0.20

* Debugging pip

## 0.0.19


## 0.0.18

* Expanded one pip call into 3 for twine/wheel dependencies. Fixed a bug in wheel filename usage.

## 0.0.17

* Installing pip==1.5.6 for twine explicitly

## 0.0.16

* Triggering a build for next release version

## 0.0.15

* Upgrading to pip==1.5.1 explicitly for wheels dependency before release

## 0.0.14

* Reverting to 0.0.14-dev... sorry.
* Botched 0.0.14 release, moving manually to 0.0.15-dev
* Continuing work on 0.0.14-dev.
* Release 0.0.13.
* Continuing work on 0.0.13-dev.
* Release 0.0.13.
* Using a different pip upgrade method.

## 0.0.13

* Upgrade pip before release with wheels. Only change platform name in wheel file if on OSX because platform-specific binaries for Linux are unsupported.

## 0.0.13

* Using a different pip upgrade method.
* Continuing work on 0.0.13-dev.
* Release 0.0.13.
* Upgrade pip before release with wheels. Only change platform name in wheel file if on OSX because platform-specific binaries for Linux are unsupported.

## 0.0.13

* Upgrade pip before release with wheels. Only change platform name in wheel file if on OSX because platform-specific binaries for Linux are unsupported.

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
