/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

/** @file 
 * External algorithms for operating on a sparse matrix.
 */

#include <nta/math/SparseMatrix.hpp>
#include <nta/math/SparseMatrixAlgorithms.hpp>

/**
 * This file contains the declarations for the two static tables that we compute
 * to speed-up log sum and log diff.
 */

namespace nta {

  // The two tables used when approximating logSum and logDiff.
  std::vector<LogSumApprox::value_type> LogSumApprox::table;
  std::vector<LogDiffApprox::value_type> LogDiffApprox::table;

} // end namespace nta

