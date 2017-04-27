Temporal Pooler Sample Code
=====

This directory contains a number of files that demonstrate how to use the
temporal memory directly. Most of the files are currently implemented as tests
that test (and illustrate) various interesting properties of the temporal
pooler.

The best place to start is hello_tm.py This file is
straightforward whereas the other files are lot more complex. For example, the
file tp_test.py contains many sophisticated tests that test the TP's properties
learning first order and high order sequences.

You can run each file by invoking python on the file, as in "python tp_test.py"

WARNING: understanding these files requires building up a very detailed
knowledge of how the temporal memory works in CLA's. The documentation is not
great at this level of detail - any suggestions or help appreciated!

