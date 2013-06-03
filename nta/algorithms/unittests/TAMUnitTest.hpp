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
 * Definitions for TAMUnitTest
 */

//----------------------------------------------------------------------

#include <nta/math/unittests/SparseMatrixUnitTest.hpp>

//----------------------------------------------------------------------

#ifndef NTA_TAM_UNIT_TEST_HPP
#define NTA_TAM_UNIT_TEST_HPP

namespace nta {

  //----------------------------------------------------------------------
  class TAMUnitTest : public SparseMatrixUnitTest
  {
  public:
    TAMUnitTest() 
      : SparseMatrixUnitTest()
    {}

    virtual ~TAMUnitTest()
    {}

    // Run all appropriate tests
    virtual void RunTests();

  private:
    // Default copy ctor and assignment operator forbidden by default
    TAMUnitTest(const TAMUnitTest&);
    TAMUnitTest& operator=(const TAMUnitTest&);

  }; // end class TAMUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_TAM_UNIT_TEST_HPP



