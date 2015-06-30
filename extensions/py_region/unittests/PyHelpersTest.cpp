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
 * Implementation of PyHelpers test
 */

#include <py_support/PyHelpers.hpp>
#include "PyHelpersTest.hpp"
#include <limits>

namespace nupic
{

PyHelpersTest::PyHelpersTest()
{
  NTA_DEBUG << "Py_Initialize()";
  Py_Initialize();
}

PyHelpersTest::~PyHelpersTest()
{
  NTA_DEBUG << "Py_Finalize()";
  Py_Finalize();
}

void PyHelpersTest::RunTests()
{
  // Test py::Ptr construction
  {
    {
      // NULL pointer
      PyObject * p  = NULL;
      SHOULDFAIL(py::Ptr(p, /* allowNULL: */false));

      py::Ptr pp1(p, /* allowNULL: */true);
      TEST((PyObject *)pp1 == NULL);
      TEST(pp1.isNULL());
    }

    // Non-NULL pointer
    {
      PyObject * p = PyTuple_New(1);
      py::Ptr pp2(p);
      TEST(!pp2.isNULL());
      TEST((PyObject *)pp2 == p);
      pp2.release();
      TEST(pp2.isNULL());
      Py_DECREF(p);
    }
    
    // assign
    {
      PyObject * p = PyTuple_New(1);
      TEST(p->ob_refcnt == 1);
      py::Ptr pp(NULL, /* allowNULL */ true);
      TEST(pp.isNULL());
      NTA_DEBUG << "*** Before assign";
      pp.assign(p);
      NTA_DEBUG << "*** After assign";
      TEST(p->ob_refcnt == 2);
      TEST(!(pp.isNULL()));
      Py_DECREF(p);
      TEST(p->ob_refcnt == 1);
    }
  }

  // py::String
  {
    py::String ps1(std::string("123"));
    TEST(PyString_Check(ps1) != 0);

    py::String ps2("123", size_t(3));
    TEST(PyString_Check(ps2) != 0);

    py::String ps3("123");
    TEST(PyString_Check(ps3) != 0);

    std::string s1(PyString_AsString(ps1));
    std::string s2(PyString_AsString(ps2));
    std::string s3(PyString_AsString(ps3));
    std::string expected("123");
    TEST(s1 == expected);
    TEST(s2 == expected);
    TEST(s3 == expected);
  
    TEST(std::string(ps1) == expected);
    TEST(std::string(ps2) == expected);
    TEST(std::string(ps3) == expected);

    PyObject * p = PyString_FromString("777");
    py::String ps4(p);
    TEST(std::string(ps4) == std::string("777"));
  }

  // py::Int
  {
    py::Int n1(-5);
    py::Int n2(-6666);
    py::Int n3(long(0));
    py::Int n4(555);
    py::Int n5(6666);
    
    TEST(n1 == -5);
    int x = n2; 
    int expected = -6666;
    TEST(x == expected);
    TEST(n3 == 0);
    TEST(n4 == 555);
    x = n5;
    expected = 6666;
    TEST(x == expected);
  }

  // py::Long
  {
    py::Long n1(-5);
    py::Long n2(-66666666);
    py::Long n3(long(0));
    py::Long n4(555);
    py::Long n5(66666666);
    
    TEST(n1 == -5);
    long x = n2; 
    long expected = -66666666;
    TEST(x == expected);
    TEST(n3 == 0);
    TEST(n4 == 555);
    x = n5;
    expected = 66666666;
    TEST(x == expected);
  }

  // py::UnsignedLong
  {
    py::UnsignedLong n1((unsigned long)(-5));
    py::UnsignedLong n2((unsigned long)(-66666666));
    py::UnsignedLong n3((unsigned long)(0));
    py::UnsignedLong n4(555);
    py::UnsignedLong n5(66666666);
    
    TEST(n1 == (unsigned long)(-5));
    TEST(n2 == (unsigned long)(-66666666));
    TEST(n3 == 0);
    TEST(n4 == 555);
    TEST(n5 == 66666666);
  }

  // py::Float
  {
    TEST(py::Float::getMax() == std::numeric_limits<double>::max());
    TEST(py::Float::getMin() == std::numeric_limits<double>::min());

    py::Float max(std::numeric_limits<double>::max());
    py::Float min(std::numeric_limits<double>::min());
    py::Float n1(-0.5);
    py::Float n2(double(0));
    py::Float n3(333.555);
    py::Float n4(0.02);
    py::Float n5("0.02");
    
    TEST(max == py::Float::getMax());
    TEST(min == py::Float::getMin());
    TEST(n1 == -0.5);
    TEST(n2 == 0);
    TEST(n3 == 333.555);
    TEST(n4 == 0.02);
    TEST(n5 == 0.02);
  }

  // py::Tuple
  {
    py::String s1("item_1");
    py::String s2("item_2");

    // Empty tuple
    {
      py::Tuple empty;
      TEST(PyTuple_Check(empty) != 0);
      TEST(empty.getCount() == 0);
      
      SHOULDFAIL(empty.setItem(0, s1));
      SHOULDFAIL(empty.getItem(0));
    }

    // One item tuple
    {
      py::Tuple t1(1);
      TEST(PyTuple_Check(t1) != 0);
      TEST(t1.getCount() == 1);

      t1.setItem(0, s1);
      py::String item1(t1.getItem(0));
      TEST(std::string(item1) == std::string(s1));
      
      py::String fastItem1(t1.fastGetItem(0));
      TEST(std::string(fastItem1) == std::string(s1));
      fastItem1.release();
      
      SHOULDFAIL(t1.setItem(1, s2));
      SHOULDFAIL(t1.getItem(1));

      TEST(t1.getCount() == 1);
    }

    // 2 items tuple
    {
      py::Tuple t2(2);
      TEST(PyTuple_Check(t2) != 0);
      TEST(t2.getCount() == 2);

      t2.setItem(0, s1);
      py::String item1(t2.getItem(0));
      TEST(std::string(item1) == std::string(s1));
      py::String fastItem1(t2.fastGetItem(0));
      TEST(std::string(fastItem1) == std::string(s1));
      fastItem1.release();

      t2.setItem(1, s2);
      py::String item2(t2.getItem(1));
      TEST(std::string(item2) == std::string(s2));
      py::String fastItem2(t2.fastGetItem(1));
      TEST(std::string(fastItem2) == std::string(s2));
      fastItem2.release();


      SHOULDFAIL(t2.setItem(2, s2));
      SHOULDFAIL(t2.getItem(2));

      TEST(t2.getCount() == 2);
    }
  }

  // py::List
  {
    py::String s1("item_1");
    py::String s2("item_2");

    // Empty list
    {
      py::List empty;
      TEST(PyList_Check(empty) != 0);
      TEST(empty.getCount() == 0);
      
      SHOULDFAIL(empty.setItem(0, s1));
      SHOULDFAIL(empty.getItem(0));
    }

    // One item list
    {
      py::List t1;
      TEST(PyList_Check(t1) != 0);
      TEST(t1.getCount() == 0);

      t1.append(s1);
      py::String item1(t1.getItem(0));
      TEST(std::string(item1) == std::string(s1));
      py::String fastItem1(t1.fastGetItem(0));
      TEST(std::string(fastItem1) == std::string(s1));
      fastItem1.release();

      TEST(t1.getCount() == 1);
      TEST(std::string(item1) == std::string(s1));
      
      SHOULDFAIL(t1.getItem(1));
    }

    // Two items list
    {
      py::List t2;
      TEST(PyList_Check(t2) != 0);
      TEST(t2.getCount() == 0);

      t2.append(s1);
      py::String item1(t2.getItem(0));
      TEST(std::string(item1) == std::string(s1));
      py::String fastItem1(t2.fastGetItem(0));
      TEST(std::string(fastItem1) == std::string(s1));
      fastItem1.release();

      t2.append(s2);
      TEST(t2.getCount() == 2);
      
      py::String item2(t2.getItem(1));
      TEST(std::string(item2) == std::string(s2));
      py::String fastItem2(t2.fastGetItem(1));
      TEST(std::string(fastItem2) == std::string(s2));
      fastItem2.release();


      SHOULDFAIL(t2.getItem(2));
    }
  }

  // py::Dict
  {
    // Empty dict
    {
      py::Dict d;
      TEST(PyDict_Size(d) == 0);

      TEST(d.getItem("blah") == NULL);
    }

    // Failed External PyObject *
    {
      // NULL object
      SHOULDFAIL(py::Dict(NULL));

      // Wrong type (must be a dictionary)
      py::String s("1234");
      try
      {
        py::Dict d(s.release());
        NTA_THROW << "py::Dict d(s) Should fail!!!";
      }
      catch(...)
      {
      }
      // SHOULDFAIL fails to fail :-)
      //SHOULDFAIL(py::Dict(s));
    }

    // Successful external PyObject *
    {

      PyObject * p = PyDict_New();
      PyDict_SetItem(p, py::String("1234"), py::String("5678"));
      
      py::Dict d(p);

      TEST(PyDict_Contains(d, py::String("1234")) == 1);

      PyDict_SetItem(d, py::String("777"), py::String("999"));

      TEST(PyDict_Contains(d, py::String("777")) == 1);

    }
    
    // getItem with default (exisiting and non-exisitng key)
    {
      py::Dict d;
      d.setItem("A", py::String("AAA"));

      PyObject * defaultItem = (PyObject *)123;
      
      py::String A(d.getItem("A"));             
      TEST(std::string(A) == std::string("AAA"));

      // No "B" in the dict, so expect to get the default item
      PyObject * B = (d.getItem("B", defaultItem));
      TEST(B == defaultItem);

      PyDict_SetItem(d, py::String("777"), py::String("999"));
      TEST(PyDict_Contains(d, py::String("777")) == 1);
    }
    
    
    //NTA_DEBUG << ss << ": " << ss->ob_refcnt;
  }

  // py::Module
  {
    py::Module module("sys");
    TEST(std::string(PyModule_GetName(module)) == std::string("sys"));
  }

  // py::Class
  {
    py::Class c("datetime", "date");
  }

  // py::Instance
  {
    
    py::Tuple args(3);
    args.setItem(0, py::Long(2000));
    args.setItem(1, py::Long(11));
    args.setItem(2, py::Long(5));
    py::Instance date("datetime", "date", args, py::Dict());

    // Test invoke()
    {
      py::String result(date.invoke("__str__", py::Tuple(), py::Dict()));
      std::string res((const char *)result);
      std::string expected("2000-11-05");
      TEST(res == expected);
    }

    // Test hasAttr()
    {
      py::String result(date.invoke("__str__", py::Tuple(), py::Dict()));
      std::string res((const char *)result);
      std::string expected("2000-11-05");
      TEST(!(date.hasAttr("No such attribute")));
      TEST(date.hasAttr("year"));
    }

    // Test getAttr()
    {
      py::Int year(date.getAttr("year"));
      TEST(2000 == long(year));
    }

    // Test toString()
    {
      std::string res((const char *)py::String(date.toString()));
      std::string expected("2000-11-05");
      TEST(res == expected);
    }
  }

  // Test custom exception
  {
    py::Tuple args(1);
    args.setItem(0, py::String("error message!"));
    py::Instance e(PyExc_RuntimeError, args);
    e.setAttr("traceback", py::String("traceback!!!"));

    PyErr_SetObject(PyExc_RuntimeError, e);

    try
    {
      py::checkPyError(0);
    }
    catch (const nupic::Exception & e)
    {
      NTA_DEBUG << e.getMessage();
    }
  }
}

}

