#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

echo
echo Running `basename $0`...
echo

check_previous_exit_status () { if [ $? -ne 0 ]; then exit $?; fi; }

python$PY_VER $NUPIC/examples/bindings/sparse_matrix_how_to.py
check_previous_exit_status
# python $NUPIC/examples/bindings/svm_how_to.py # tkinter missing in Travis build machine
# python $NUPIC/examples/bindings/temporal_pooler_how_to.py # tkinter too

# examples/opf (run at least 1 from each category)
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/anomaly/spatial/2field_few_skewed/
check_previous_exit_status
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/anomaly/temporal/saw_200/
check_previous_exit_status
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/classification/category_TP_1/
check_previous_exit_status
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/missing_record/simple_0/
check_previous_exit_status
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/multistep/hotgym/
check_previous_exit_status
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/opfrunexperiment_test/simpleOPF/hotgym_1hr_agg/
check_previous_exit_status

# opf/experiments/params - skip now
python$PY_VER $NUPIC/scripts/run_opf_experiment.py $NUPIC/examples/opf/experiments/spatial_classification/category_1/
check_previous_exit_status

# examples/tp
python$PY_VER $NUPIC/examples/tp/hello_tp.py
check_previous_exit_status
python$PY_VER $NUPIC/examples/tp/tp_test.py
check_previous_exit_status
