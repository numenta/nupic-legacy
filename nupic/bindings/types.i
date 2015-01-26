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


%include <nupic/types/Types.h>
%include <nupic/types/Types.hpp>

///////////////////////////////////////////////////////////////////
///  Bring in SWIG typemaps for base types and stl.
///////////////////////////////////////////////////////////////////
%include <typemaps.i>
%include <stl.i>
%include <std_list.i>
%include <std_set.i>

///////////////////////////////////////////////////////////////////
///  Instantiate templates that we will use.
///////////////////////////////////////////////////////////////////

%template(VectorOfInt32) std::vector<NTA_Int32>;
%template(VectorOfInt64) std::vector<NTA_Int64>;
%template(VectorOfUInt32) std::vector<NTA_UInt32>;
%template(VectorOfUInt64) std::vector<NTA_UInt64>;

%template(FloatVector) std::vector<NTA_Real32>;
%template(DoubleVector) std::vector<NTA_Real64>;

%template(StringVector) std::vector<std::string>;
%template(StringList) std::list<std::string>;
%template(StringSet) std::set<std::string>;
%template(StringMap) std::map<std::string, std::string>;

%template(StringStringPair) std::pair<std::string, std::string>;
%template(StringStringList) std::vector< std::pair<std::string, std::string> >;
%template(StringMapList) std::vector< std::map<std::string, std::string> >;
%template(StringIntPair) std::pair<std::string, NTA_Int32>;

%template(PairOfUInt32) std::pair<nupic::UInt32, nupic::UInt32>;
%template(VectorOfPairsOfUInt32) std::vector<std::pair<nupic::UInt32,nupic::UInt32> >;
%template(VectorOfVectorsOfPairsOfUInt32) std::vector<std::vector<std::pair<nupic::UInt32,nupic::UInt32> > >;

%template(PairUInt32Real32) std::pair<nupic::UInt32,nupic::Real32>;
%template(PairUInt32Real64) std::pair<nupic::UInt32,nupic::Real64>;
%template(VectorOfPairsUInt32Real32) std::vector<std::pair<nupic::UInt32,nupic::Real32> >;
%template(VectorOfPairsUInt32Real64) std::vector<std::pair<nupic::UInt32,nupic::Real64> >;
#ifdef NTA_QUAD_PRECISION
%template(PairUInt32Real128) std::pair<nupic::UInt32,nupic::Real128>;
%template(SizeTReal128Vector) std::vector<std::pair<nupic::UInt32,nupic::Real128> >;
#endif




