#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

echo
echo Running script-run-examples.sh...
echo

python ${NUPIC}/examples/bindings/sparse_matrix_how_to.py || exit
# python ${NUPIC}/examples/bindings/svm_how_to.py || exit # tkinter missing in Travis build machine
# python ${NUPIC}/examples/bindings/temporal_pooler_how_to.py || exit # tkinter too

# examples/opf (run at least 1 from each category)
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/anomaly/spatial/2field_few_skewed/ || exit
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/anomaly/temporal/saw_200/ || exit
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/classification/category_TM_1/ || exit
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/missing_record/simple_0/ || exit
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/multistep/hotgym/ || exit
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/opfrunexperiment_test/simpleOPF/hotgym_1hr_agg/ || exit

# opf/experiments/params - skip now
python ${NUPIC}/scripts/run_opf_experiment.py ${NUPIC}/examples/opf/experiments/spatial_classification/category_1/ || exit

# examples/tm
python ${NUPIC}/examples/tm/hello_tm.py || exit
python ${NUPIC}/examples/tm/tm_test.py || exit
