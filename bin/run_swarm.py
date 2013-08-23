#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2011-2013 Numenta Inc. All rights reserved.
#
# The information and source code contained herein is the
# exclusive property of Numenta Inc. No part of this software
# may be used, reproduced, stored or distributed in any form,
# without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""This script is the command-line interface for running swarms in nupic
"""
from nupic.swarming import permutations_runner

if __name__ == "__main__":
  permutations_runner.main()

