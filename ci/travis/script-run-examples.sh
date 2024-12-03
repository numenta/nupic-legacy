#!/bin/bash
# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
