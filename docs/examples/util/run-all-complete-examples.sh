#!/usr/bin/env bash

echo "Running opf/complete-example.py ..."
pushd ../opf
python complete-example.py
popd

echo "Running networkapi/complete-example.py ..."
pushd ../networkapi
python complete-example.py
popd

echo "Running algo/complete-example.py ..."
pushd ../algo
python complete-example.py
popd

echo ""
echo "All prediction results saved. Now you can run:"
echo "    python check_predictions.py"
