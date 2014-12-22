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

// This is needed by iorange and math

%feature("docstring")  GetBasicTypeFromName 
"GetBasicTypeFromName(typeName) -> int

Internal use.
Finds a base type enumeration given a type name.
";

%feature("docstring")  GetBasicTypeSize
"GetBasicTypeFromName(typeName) -> int

Internal use.
Gets the number of bytes use to specify the named
type in C code.
";

%inline %{

#include <nupic/types/BasicType.hpp>

NTA_BasicType GetBasicTypeFromName(const std::string &type)
{
  return nupic::BasicType::parse(type);
}

size_t GetBasicTypeSize(const std::string &type)
{
  return nupic::BasicType::getSize(nupic::BasicType::parse(type));
}

%}

#ifdef NTA_DOUBLE_PRECISION
// Note, when changing the documentation or implementation, make sure to 
// also change the single precision version below.
%pythoncode %{
import numpy
def GetNumpyDataType(typeName):
  """Gets the numpy dtype associated with a particular NuPIC 
  base type name. The only supported type name is 
  'NTA_Real', which returns a numpy dtype of numpy.float64.
  """
  if typeName == "NTA_Real": return numpy.float64
  elif typeName == "NTA_Real32": return numpy.float32
  elif typeName == "NTA_Real64": return numpy.float64
  #elif typeName == "NTA_Real128": return numpy.float128
  else: raise RuntimeError("Unsupported type name.")
%}
#else
// Note, when changing the documentation or implementation, make sure to 
// also change the double precision version above.
%pythoncode %{
import numpy
def GetNumpyDataType(typeName):
  """Gets the numpy dtype associated with a particular NuPIC 
  base type name. The only supported type name is 
  'NTA_Real', which returns a numpy dtype of numpy.float32.
  The returned value can be used with numpy functions like
  numpy.array(..., dtype=dtype) and numpy.astype(..., dtype=dtype).
  """
  if typeName == "NTA_Real": return numpy.float32
  elif typeName == "NTA_Real32": return numpy.float32
  elif typeName == "NTA_Real64": return numpy.float64
  #elif typeName == "NTA_Real128": return numpy.float128
  else: raise RuntimeError("Unsupported type name.")
%}
#endif

%pythoncode %{
def GetNTARealType():
  """Gets the name of the NuPIC floating point base type, 
  which is used for most internal calculations.
  This base type name can be used with GetBasicTypeFromName(),
  GetBasicTypeSize(), and GetNumpyDataType().
  """
  return "NTA_Real"
def GetNTAReal():
  """Gets the numpy dtype of the NuPIC floating point base type,
  which is used for most internal calculations.
  The returned value can be used with numpy functions like
  numpy.array(..., dtype=dtype) and numpy.astype(..., dtype=dtype).
  """
  return GetNumpyDataType(GetNTARealType())
%}

