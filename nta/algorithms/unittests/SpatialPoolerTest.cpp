/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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
 * Implementation of unit tests for SpatialPooler
 */     

#include <iostream>
#include <nta/algorithms/spatial_pooler.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>
#include <cstring>
#include "SpatialPoolerTest.hpp"

using namespace std;
using namespace nta::algorithms::spatial_pooler;

namespace nta {  

	void SpatialPoolerTest::RunTests() 
	{
		testBasic();
	}  

	void SpatialPoolerTest::testBasic() 
	{
		NTA_CHECK(true);
	}
    
} // end namespace nta
