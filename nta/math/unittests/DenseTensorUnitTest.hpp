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
 * Declaration of class DenseTensorUnitTest
 */

//----------------------------------------------------------------------

#include <nta/math/unittests/SparseTensorUnitTest.hpp>

//----------------------------------------------------------------------

#ifndef NTA_DENSE_TENSOR_UNIT_TEST_HPP
#define NTA_DENSE_TENSOR_UNIT_TEST_HPP

namespace nta {

  //----------------------------------------------------------------------
  class DenseTensorUnitTest : public Tester
  {
  public:
    DenseTensorUnitTest() {}
    virtual ~DenseTensorUnitTest() {}

    // Run all appropriate tests
    virtual void RunTests();

  private:
    typedef Index<UInt, 1> I1;
    typedef Index<UInt, 2> I2;
    typedef Index<UInt, 3> I3;
    typedef Index<UInt, 4> I4;
    typedef Index<UInt, 5> I5;
    typedef Index<UInt, 6> I6;

    typedef DenseTensor<I5, Real> D5;
    typedef DenseTensor<I4, Real> D4;
    typedef DenseTensor<I3, Real> D3;
    typedef DenseTensor<I2, Real> D2;
    typedef DenseTensor<I1, Real> D1;

    //void unitTestConstructor();
    //void unitTestGetSet();
    //void unitTestIsSymmetric();
    //void unitTestPermute();
    //void unitTestResize();
    //void unitTestReshape();
    //void unitTestSlice();
    //void unitTestElementApply();
    //void unitTestFactorApply();
    //void unitTestAccumulate();
    //void unitTestOuterProduct();
    //void unitTestContract();
    //void unitTestInnerProduct();

    // Default copy ctor and assignment operator forbidden by default
    DenseTensorUnitTest(const DenseTensorUnitTest&);
    DenseTensorUnitTest& operator=(const DenseTensorUnitTest&);

  }; // end class DenseTensorUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_DENSE_TENSOR_UNIT_TEST_HPP



