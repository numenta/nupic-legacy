Validation Testing
==================

To validate that you have a good build, run the following commands
::
    cd $TRUNK/build_system/pybuild
    python test_release.py --short ~/nta/current ~/nta/trunk 
 
NOTE: If you are running this for the first time and have not installed Hadoop, MySQL, etc. you will see failures in expGeneratorTest.  
 
Detailed Testing Notes
======================

A key to Numenta's development strategy is continuous integration and testing. If the autobuild breaks, this cycle grinds to a halt and problems pile up. Developers should do whatever testing is necessary prior to a checkin to make sure they don't break the build. All developers are required to test their code before checking in. Specifically, the requirements are:

* Logout and log back in if you just did a build for the first time. This ensures that nupic-env.sh has been read in properly.
* For all checkins, run this with the full set of standard tests (item 1 below)

    test_release.py --short

* If you add or delete files, test the source releases as described below (item 5).
* If you might have changed anything affecting backward compatibility, run the regression tests as described below (item 6).
 
In the following:
* $TRUNK is the path to your source directory
* $NTA is the path to your installation directory, e.g. ~/nta/eng

Testing syntax:

1. To run the full set of tests. This is required before all checkins. Detailed output in the file "test.out"::

    cd $TRUNK/build_system/pybuild
    python test_release.py --short $NTA $TRUNK

   For example::

    python test_release.py --short ~/nta/current ~/nta/trunk 

2. To run a single test::

    python test_release.py --short $NTA $TRUNK --test=

   For example::

    python test_release.py --short ~/nta/current ~/nta/trunk --test=pil_test

3. To run a single test without output to the terminal::

    python test_release.py --short $NTA $TRUNK --test --log=stdout=

4. To run two tests::

    python test_release.py --short $NTA $TRUNK --test --test==

5. To run all standard tests in parallel (4-way) [note: ^C does not work if you run tests in parallel]::

    python test_release.py <installdir> <trunkdir> --n 4

To force a disabled test to run, use the --force=all option, e.g.::

    python test_release.py <installdir> <trunkdir> --test=nine_test --force=all