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


#include <string>
#include <limits>

#include <nta/engine/UniformLinkPolicy.hpp>
#include <nta/engine/Link.hpp>
#include <nta/engine/YAMLUtils.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/utils/Log.hpp>
#include <nta/types/Fraction.hpp>

#include <boost/shared_ptr.hpp>

namespace nta
{


// used to detect an uninitialized value
static const size_t uninitializedElementCount = 987654321;


UniformLinkPolicy::UniformLinkPolicy(const std::string params,
                                     Link* link) :
  link_(link),
  elementCount_(uninitializedElementCount), 
  parameterDimensionality_(0),
  initialized_(false)
{
  setValidParameters();
  readParameters(params);
  validateParameterDimensionality();
  populateWorkingParameters();
  validateParameterConsistency();
}

UniformLinkPolicy::~UniformLinkPolicy()
{
}

void UniformLinkPolicy::readParameters(const std::string& params)
{
  ValueMap paramMap = YAMLUtils::toValueMap(params.c_str(), parameters_);

  boost::shared_ptr<std::string> mappingStr = paramMap.getString("mapping");

  if(*mappingStr == "in")
  {
    mapping_ = inMapping;
  }
  else if(*mappingStr == "out")
  {
    mapping_ = outMapping;
  }
  else if(*mappingStr == "full")
  {
    mapping_ = fullMapping;
  }
  else
  {
    NTA_THROW << "Internal error: ParameterSpec constraint not enforced, "
      "Invalid mapping type utilized with UniformLinkPolicy.";
  }

  populateArrayParamVector<Real64>(rfSize_,
                                   paramMap,
                                   "rfSize");

  populateArrayParamVector<Real64>(rfOverlap_,
                                   paramMap,
                                   "rfOverlap");

  boost::shared_ptr<std::string> rfGranularityStr =
    paramMap.getString("rfGranularity");

  if(*rfGranularityStr == "nodes")
  {
    rfGranularity_ = nodesGranularity;
  }
  else if (*rfGranularityStr == "elements")
  {
    rfGranularity_ = elementsGranularity;
  }
  else
  {
    NTA_THROW << "Internal error: ParameterSpec constraint not enforced, "
      "Invalid rfGranularity type utilized with "
      "UniformLinkPolicy.";
  }

  populateArrayParamVector<Real64>(overhang_,
                                   paramMap,
                                   "overhang");

  populateArrayParamVector<OverhangType>(overhangType_,
                                         paramMap,
                                         "overhangType");

  populateArrayParamVector<Real64>(span_,
                                   paramMap,
                                   "span");

  boost::shared_ptr<std::string> strictStr =
    paramMap.getString("strict");

  if(*strictStr == "true")
  {
    strict_ = true;
  }
  else if(*strictStr == "false")
  {
    strict_ = false;
  }
  else
  {
    NTA_THROW << "Internal error: ParameterSpec constraint not enforced, "
      "Invalid strict setting utilized with UniformLinkPolicy.";
  }
}

// ---
// Parameters support "wildcard" dimensionality, so we must validate
// them here.  See the declaration of parameterDimensionality_ in the hpp for
// more details.
// ---
void UniformLinkPolicy::validateParameterDimensionality()
{
  std::map<std::string,size_t> dimensionalityMap;

  dimensionalityMap["rfSize"] = rfSize_.size();
  dimensionalityMap["rfOverlap"] = rfOverlap_.size();
  dimensionalityMap["overhang"] = overhang_.size();
  dimensionalityMap["overhangType"] = overhangType_.size();
  dimensionalityMap["span"] = span_.size();

  std::stringstream parameterDimensionalityMsg;
  bool parametersAreInconsistent = false;

  for(auto & elem : dimensionalityMap)
  {
    parameterDimensionalityMsg << elem.first << ": ";
    elem.second == 1 ? (parameterDimensionalityMsg << "*") :
      (parameterDimensionalityMsg << elem.second);

    if(elem.second != parameterDimensionality_)
    {
      switch(parameterDimensionality_)
      {
      case 0:
      case 1:
      {
        parameterDimensionality_ = elem.second;
        break;
      }
      default:
      {
        if(elem.second != 1)
        {
          parametersAreInconsistent = true;
          parameterDimensionalityMsg << " <-- Inconsistent";
        }
        break;
      }
      }
    }

    parameterDimensionalityMsg << "\n";
  }

  if(parametersAreInconsistent)
  {
    NTA_THROW << "The dimensionality of the parameters are inconsistent:"
              << "\n\n" << parameterDimensionalityMsg.str(); 
  }
}

// ---
// Certain combinations of parameters are not valid when used in combination,
// so we check to ensure our parameters are mutually consistent here
// ---
void UniformLinkPolicy::validateParameterConsistency()
{
  for(size_t i = 0; i < parameterDimensionality_; i++)
  {
    if(strict_)
    {
      if(!(workingParams_.span[i].isNaturalNumber()))
      {
        NTA_THROW << "When using a granularity of nodes in combination with "
          "strict, the specified span must be a natural number";
      }
    }

    // ---
    // We don't yet know the size of the source dimensions, so we can't
    // perform this check now.  We'll do it at initialization instead.
    // ---
    //if(workingParams_.overhang[i] > srcDimensions_[i])
    //{
    //  NTA_THROW << "The overhang can't exceed the size of the source "
    //               "dimensions";
    //}

    if(workingParams_.rfOverlap[i] == workingParams_.rfSize[i])
    {
      NTA_THROW << "100% overlap is not permitted; use a mapping of \"full\""
        " instead";
    }

    if(workingParams_.rfOverlap[i] > workingParams_.rfSize[i])
    {
      NTA_THROW << "An overlap greater than the rfSize is not valid";
    }
  }
}

void UniformLinkPolicy::populateWorkingParameters()
{
  // ---
  // First, convert our vectors of real values to vectors of fractions
  //
  // This is necessary to remove floating point precision issues when
  // calculating strict uniformity using non integer values
  // ---
  copyRealVecToFractionVec(rfSize_,
                           workingParams_.rfSize);

  copyRealVecToFractionVec(rfOverlap_,
                           workingParams_.rfOverlap);

  copyRealVecToFractionVec(overhang_,
                           workingParams_.overhang);

  copyRealVecToFractionVec(span_,
                           workingParams_.span);

  NTA_CHECK(workingParams_.overhangType.size() == 0);

  for(auto & elem : overhangType_)
  {
    workingParams_.overhangType.push_back(elem);
  }
}

template <typename T>
void UniformLinkPolicy::populateArrayParamVector(
  std::vector<T>& vec,
  const ValueMap& paramMap,
  const std::string& paramName)
{
  NTA_CHECK(vec.size() == 0);

  boost::shared_ptr<Array> arrayVal = paramMap.getArray(paramName);

  T* buf = (T*) arrayVal->getBuffer();

  vec.reserve(arrayVal->getCount());
  for(size_t i = 0; i < arrayVal->getCount(); i++)
  {
    vec.push_back(buf[i]);
  }
}

void UniformLinkPolicy::copyRealVecToFractionVec(
  const std::vector<Real64>& sourceVec,
  DefaultValuedVector<Fraction>& destVec)
{
  NTA_CHECK(destVec.size() == 0);

  for(auto & elem : sourceVec)
  {
    destVec.push_back(Fraction::fromDouble(elem));
  }
}

void UniformLinkPolicy::setValidParameters()
{
  // ---
  // The Network::link() method specifies the direction of the link (i.e.
  // source and destination regions), and this parameter specifies the
  // mapping of the receptive field topology with respect to those regions.
  //
  // A mapping of "in" implies that mutiple Nodes from the source Region
  // will be mapped "in" to each Node in the destination Region.  Further
  // parameters are given per destination Region Node.
  //
  // A mapping of "out" implies that each Node from the source Region will
  // be mapped "out" to multiple Nodes in the destination Region.  Further
  // parameters are given per source Region Node.
  //
  // A mapping of "full" implies that each Node from the source Region will
  // be mapped to every Node in the destination Region.
  //
  // Since most HTMs involve wider and wider effective receptive fields as
  // one ascends the heirarchy, the default mapping is "in".
  //
  // Note: If a receptive field size of 1 is specified (see the parameter
  //       rfSize), then there is no distinction between a mapping of "in"
  //       or "out".
  //
  // Note: Since the granularity of the receptive field can be specified via
  //       parameter (see rfGranularity), the mapping may operate on finer
  //       structure than at the Node level.
  // ---
  parameters_.add("mapping",
                  ParameterSpec("Source to Destination Mapping "
                                "(\"in\", \"out\", \"full\")",
                                NTA_BasicType_Byte,
                                0,
                                "enumeration:in, out, full",
                                "in",
                                ParameterSpec::ReadWriteAccess));
    
  // ---
  // Specifies the size of the receptive field topology.
  //
  // For a mapping of "in", this specifies how many source Nodes in a given
  // dimension send their output to each destination Node in the
  // corresponding dimension.
  //
  // For a mapping of "out", this specifies how many destination Nodes in a
  // given dimension receive input from each source Node in the corresponding
  // dimension.
  //
  // For both "in" and "out" mappings, this can be given in one of two forms:
  //
  // 1) As an array of real numbers; the length of the array being equal to
  //    the number of dimensions, and each entry designating the size of the
  //    receptive field topology in the corresponding dimension.
  // 2) As an array of real numbers; the length of the array being equal to
  //    one.  In this case, the given number is used for all dimensions.
  //
  // For a mapping of "full", this parameter is invalid.
  //
  // Note: Regardless of the receptive field granularity specified (see the
  //       parameter rfGranularity) this is given in units of Nodes.  To
  //       specify element level access use fractional values in combination
  //       with a granularity of "elements".
  //
  // Note: Fractional values are valid in combination with a granularity of
  //       "nodes" only when the parameter strict is set to false.
  //
  // Note: The default is a value of [1] indicating a direct Node to Node
  //       linkage.  This allows a the UniformLinkPolicy to be used when
  //       connecting Region level parameters without needing to specify this
  //       parameter.
  // ---
  parameters_.add("rfSize",
                  ParameterSpec("Receptive Field Size",
                                NTA_BasicType_Real64,
                                0,
                                "interval:[0,...)",
                                "[1]",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Specifies the amount of Nodes by which adjacent receptive fields overlap
  //
  // This can be specified in one of two forms:
  //
  // 1) As an array of real numbers; the length of the array being equal to
  //    the number of dimensions, and each entry designating the amount of
  //    Nodes by which adjacent receptive fields overlap in the corresponding
  //    dimension.
  // 2) As an array of real numbers; the length of the array being equal to
  //    one.  In this case, the given number is used for all dimensions.
  // ---
  parameters_.add("rfOverlap",
                  ParameterSpec("Receptive Field Overlap",
                                NTA_BasicType_Real64,
                                0,
                                "interval:[0,...)",
                                "[0]",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Since Regions contain discrete Nodes which themselves contain discrete
  // elements, the granularity at which uniformity is enforced is
  // configurable via parameters.
  // ---
  parameters_.add("rfGranularity",
                  ParameterSpec("Receptive Field Granularity "
                                "(\"nodes\", \"elements\")",
                                NTA_BasicType_Byte,
                                0,
                                "enumeration:nodes, elements",
                                "nodes",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Specifies the amount of Nodes on either side of a given dimension that
  // should be absent in the applicable Region (the source Region for a
  // mapping of "in", and the destination Region for a mapping of "out").
  //
  // This can be specified in one of two forms:
  //
  // 1) As an array of real numbers; the length of the array being equal to
  //    the number of dimensions, and each entry designating the amount of
  //    overhang in the corresponding dimension.
  // 2) As an array of real numbers; the length of the array being equal to
  //    one.  In this case, the given number is used for all dimensions.
  //
  // How receptive fields see intentionally absent Nodes is specified by
  // further parameters (see overhangType).
  //
  // This parameter is invalid for a mapping of "full".
  // ---
  parameters_.add("overhang",
                  ParameterSpec("Region Overhang",
                                NTA_BasicType_Real64,
                                0,
                                "interval:[0,...)",
                                "[0]",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Specifies how receptive fields see intentionally absent Nodes (see
  // overhang).
  //
  // A value of "null" implies that a target whose receptive field includes
  // overhang will receive no input for intentionally absent Nodes.
  //
  // A value of "wrap" implies that a target whose receptive field includes
  // overhang will receive input wrapped to the opposite end of the
  // applicable dimension.
  //
  // This can be specified in one of two forms:
  //
  // 1) As an array of real numbers; the length of the array being equal to
  //    the number of dimensions, and each entry designating the overhang
  //    type in the corresponding dimension.
  // 2) As an array of real numbers; the length of the array being equal to
  //    one.  In this case, the given overhang type is used for all
  //    dimensions.
  //
  // TODO - If support for arrays of strings is added, convert this to use
  //        an array of strings
  // ---
  parameters_.add("overhangType",
                  ParameterSpec("Receptive Field Overhang Type "
                                "(null=0, wrap=1)",
                                NTA_BasicType_UInt32,
                                0,
                                "enumeration:0, 1",
                                "[0]",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Specifies the length, in Nodes, of a span.  A span represents an atomic
  // unit of Nodes which may have overlap.  This permits linkage structures
  // where uniform groups of overlapping Nodes can be repeated (without
  // themselves overlapping).  This is primarily useful in specifying the
  // intended scaling behavior of a linkage (e.g. for scanning networks).
  //
  // A span of zero (the default) is interpretted as indicating that there
  // are no internal atomic groups of overlapping Nodes in the applicable
  // dimension.  This is the equivalent of being equal to the size of the
  // applicable dimension for the appropriate Region (source for a mapping of
  // "in" and destination for a mapping of "out") plus two times that
  // dimension's overhang.
  //
  // This can be specified in one of two forms:
  //
  // 1) As an array of real numbers; the length of the array being equal to
  //    the number of dimensions, and each entry designating the span length
  //    in the corresponding dimension.
  // 2) As an array of real numbers; the length of the array being equal to
  //    one.  In this case, the given number is used for all dimensions.
  // ---
  parameters_.add("span",
                  ParameterSpec("Span group size",
                                NTA_BasicType_Real64,
                                0,
                                "interval:[0,...)",
                                "[0]",
                                ParameterSpec::ReadWriteAccess));

  // ---
  // Specifies if strict uniformity is required.  If this is set to false,
  // then the linkage is built "as close to uniform as possible".
  // ---
  parameters_.add("strict",
                  ParameterSpec("Require Strict Uniformity "
                                "(\"true\", \"false\")",
                                NTA_BasicType_Byte,
                                0,
                                "enumeration:true, false",
                                "true",
                                ParameterSpec::ReadWriteAccess));
}

// ---
// Variable definitions:
//
// R_s,i = Source Region size, in Nodes, for dimension i
// R_d,i = Destination Region size, in Nodes, for dimension i
// F_s,i = Receptive Field size at source, in Nodes, for dimension i
// F_d,i = Receptive Field size at destination, in Nodes, for dimension i
// E_s = Number of elements per Node in source Region
// E_d = Number of elements per Node in destination Region
// H_i = Overhang, in Nodes, for dimension i
// S_i = Span, in Nodes, for dimension i
// V_i = Overlap, in Nodes, for dimension i
// ---

void UniformLinkPolicy::setSrcDimensions(Dimensions& specifiedDims)
{

  if (elementCount_ == uninitializedElementCount) 
    NTA_THROW << "Internal error: output element count not initialized on link " << link_->toString();

  Dimensions dims = specifiedDims;
  if (dims.isOnes() && dims.size() != parameterDimensionality_)
    dims.promote(parameterDimensionality_);

  // This method should never be called if we've already been set
  NTA_CHECK(srcDimensions_.isUnspecified()) << "Internal error on link " << 
    link_->toString();
  NTA_CHECK(destDimensions_.isUnspecified()) << "Internal error on link " <<
    link_->toString();

  if(dims.isUnspecified())
    NTA_THROW << "Invalid unspecified source dimensions for link " << 
      link_->toString();
    
  if(dims.isDontcare())
    NTA_THROW << "Invalid dontcare source dimensions for link " <<
      link_->toString();

  // ---
  // validate that the parameter dimensionality matches the requested
  // dimensions
  // ---
  if(parameterDimensionality_ != 1)
  {
    if(parameterDimensionality_ != dims.size() && !dims.isOnes())
    {
      NTA_THROW << "Invalid parameter dimensionality; the parameters "
        "have dimensionality " << parameterDimensionality_ <<
        " but the source dimensions supplied have dimensionality "
                << dims.size();
    }
  }

  Dimensions inducedDims;

  // Induce destination dimensions from source dimensions
  switch(mapping_)
  {
  case inMapping:
  {
    if(strict_)
    {
      // ---
      // if we are set to strict uniformity, we need to validate that the
      // requested dimensions are valid
      //
      // For all dimensions i
      // (R_s,i + 2 * H_i) mod S_i = 0
      // (S_i - F_s,i) mod (F_s,i - V_i) = 0
      // Floor(F_s,i * E_s) = F_s,i * E_s
      // Then: R_d,i = (S_i - V_i)/(F_s,i - V_i) * (R_s,i + 2 * H_i)/S_i
      // ---

      for(size_t i = 0; i < dims.size(); i++)
      {
        // ---
        // If the span for this dimension is zero (indicating no atomic
        // groups of overlapping nodes), then S_i = R_s,i + 2 * H_i
        // Further, we can skip the first validation since it is trivially
        // satisfied, and the induced dimension size reduces to:
        //
        // R_d,i = (R_s,i + 2 * H_i - V_i)/(F_s,i - V_i)
        // ---

        if(workingParams_.span[i].getNumerator() == 0)
        {
          Fraction validityCheck =
            (Fraction(dims[i]) +
             workingParams_.overhang[i] * 2 - 
             workingParams_.rfSize[i]) % (workingParams_.rfSize[i] -
                                          workingParams_.rfOverlap[i]);

          if(validityCheck.getNumerator() != 0)
          {
            NTA_THROW << "Invalid source dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", given the specified"
              " overlap of " << workingParams_.rfOverlap[i] <<
              ", each successive receptive field of size " <<
              workingParams_.rfSize[i] << " as requested will "
              "add " << workingParams_.rfSize[i] -
              workingParams_.rfOverlap[i] << " required nodes. "
              "Since no span was provided, the source region "
              "size (" << dims[i] << " for this dimension) + 2 "
              "* the overhang (" << workingParams_.overhang[i]
                      << " for this dimension) must equal the receptive"
              " field size plus an integer multiple of the "
              "amount added by successive receptive fields.";
          }

          validityCheck = workingParams_.rfSize[i] * elementCount_;

          if(!validityCheck.isNaturalNumber())
          {
            NTA_THROW << "Invalid source dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", the specified "
              "receptive field size of "
                      << workingParams_.rfSize[i] << "is invalid since it "
              "would require " << validityCheck << " elements "
              "(given the source region's " << elementCount_ <<
              " elements per node).  Elements cannot be "
              "subdivided, therefore a strict mapping with this"
              " configuration is not possible.";
          }

          // R_d,i = (R_s,i + 2 * H_i - V_i)/(F_s,i - V_i)
          Fraction inducedDim = (Fraction(dims[i]) +
                                 workingParams_.overhang[i] * 2 -
                                 workingParams_.rfOverlap[i]) /
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]);

          NTA_CHECK(inducedDim.isNaturalNumber());

          inducedDim.reduce();
          inducedDims.push_back(inducedDim.getNumerator());
        }
        else
        {
          Fraction validityCheck = ((Fraction(dims[i])) + 
                                    workingParams_.overhang[i] * 2) % 
            workingParams_.span[i];

          if(validityCheck.getNumerator() != 0)
          {
            NTA_THROW << "Invalid source dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", the source size ("
                      << dims[i] << "plus 2 times the overhang (" <<
              workingParams_.overhang[i] << " per side) must be"
              " an integer multiple of the specified span (" <<
              workingParams_.span[i] << ").";
          }

          validityCheck = (workingParams_.span[i] - 
                           workingParams_.rfSize[i]) %
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]);

          if(validityCheck.getNumerator() != 0)
          {
            NTA_THROW << "Invalid source dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", given the specified"
              " overlap of " << workingParams_.rfOverlap[i] <<
              ", each successive receptive field of size " <<
              workingParams_.rfSize[i] << " as requested will "
              "add " << workingParams_.rfSize[i] -
              workingParams_.rfOverlap[i] << " required nodes. "
              "Each span in this dimension (having specified "
              "size: " << workingParams_.span[i] << ") must "
              "equal the receptive field size plus an integer "
              "multiple of the amount added by successive "
              "receptive fields.";
          }

          validityCheck = workingParams_.rfSize[i] * elementCount_;

          if(!validityCheck.isNaturalNumber())
          {
            NTA_THROW << "Invalid source dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", the specified "
              "receptive field size of "
                      << workingParams_.rfSize[i] << "is invalid since it "
              "would require " << validityCheck << " elements "
              "(given the source region's " << elementCount_ <<
              " elements per node).  Elements cannot be "
              "subdivided, therefore a strict mapping with this"
              " configuration is not possible.";
          }

          // R_d,i = (S_i - V_i)/(F_s,i - V_i) * (R_s,i + 2 * H_i)/S_i
          Fraction inducedDim = (workingParams_.span[i] -
                                 workingParams_.rfOverlap[i]) /
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]) *
            (Fraction(dims[i]) +
             workingParams_.overhang[i] * 2) /
            workingParams_.span[i];

          NTA_CHECK(inducedDim.isNaturalNumber());

          inducedDim.reduce();
          inducedDims.push_back(inducedDim.getNumerator());
        }
      }
    }
    else
    {
      // ---
      // Since we are set to non-strict uniformity, we don't need to
      // validate dimensions.  So we'll just calculate the ideal fit using
      // the "strict" formulas.  These will yeild results which are
      // fractions that may not be natural numbers.  When we don't have a
      // valid strict mapping, we want to favor packing in more information
      // than spreading that information out (i.e. if the nearest strict
      // mapping would have had n source nodes per destination node, then
      // we'll favor n + delta source nodes per destination node over
      // n - delta source nodes.  This implies rounding down.
      // ---

      for(size_t i = 0; i < dims.size(); i++)
      {
        Fraction inducedDim;

        if(workingParams_.span[i].getNumerator() == 0)
        {
          // R_d,i = (R_s,i + 2 * H_i - V_i)/(F_s,i - V_i)
          inducedDim = (Fraction(dims[i]) +
                        workingParams_.overhang[i] * 2) /
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]);
        }
        else
        {
          Fraction numSpans = (Fraction(dims[i]) +
                               workingParams_.overhang[i] * 2) /
            workingParams_.span[i];

          Fraction nodesPerSpan = Fraction(1) +
            (workingParams_.span[i] -
             workingParams_.rfSize[i]) /
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]);

          int numWholeSpans = numSpans.getNumerator() / numSpans.getDenominator();

          inducedDim = Fraction(numWholeSpans) * nodesPerSpan;
        }
            
        inducedDims.push_back(inducedDim.getNumerator() /
                              inducedDim.getDenominator());
      }
    }

    break;
  }
  default:
  {
    NTA_THROW << "UniformLinkPolicy mappings other than 'in' are not yet "
      "implemented.";

    break;
  }
  }

  srcDimensions_ = dims;
  destDimensions_ = inducedDims;
}

void UniformLinkPolicy::setDestDimensions(Dimensions& specifiedDims) 
{

  Dimensions dims = specifiedDims;
  if (dims.isOnes() && dims.size() != parameterDimensionality_)
    dims.promote(parameterDimensionality_);

  // This method should never be called if we've already been set
  NTA_CHECK(srcDimensions_.isUnspecified()) << "Internal error on link " << 
    link_->toString();
  NTA_CHECK(destDimensions_.isUnspecified()) << "Internal error on link " <<
    link_->toString();

  if(dims.isUnspecified())
    NTA_THROW << "Invalid unspecified destination dimensions for link " << 
      link_->toString();
    
  if(dims.isDontcare())
    NTA_THROW << "Invalid dontcare destination dimensions for link " <<
      link_->toString();

  // ---
  // validate that the parameter dimensionality matches the requested
  // dimensions
  // ---
  if(parameterDimensionality_ != 1)
  {
    if(parameterDimensionality_ != dims.size())
    {
      NTA_THROW << "Invalid parameter dimensionality; the parameters "
        "have dimensionality " << parameterDimensionality_ <<
        " but the destination dimensions supplied have "
        " dimensionality " << dims.size();
    }
  }

  Dimensions inducedDims;

  // Induce destination dimensions from source dimensions
  switch(mapping_)
  {
  case inMapping:
  {
    if(strict_)
    {
      // ---
      // Since the requested mapping is of type "in" and we are provided
      // destination dimensions, we can always calculate valid source
      // dimensions.  The only checks for validity that are needed are:
      //
      // If a fractional receptive field sizes is specified then:
      // 1) we must be working at a granularity of elements since strict
      //    is true
      // 2) the calculations must produce integer source dimensions, i.e.
      //    for all dimensions i
      //    Floor(F_s,i * E_s) = F_s,i * E_s
      //
      // Then: R_s,i = (R_d,i * S_i * (F_s,i - V_i))/(S_i - V_i) - 2 * H_i
      // ---

      for(size_t i = 0; i < dims.size(); i++)
      {
        if(!workingParams_.rfSize[i].isNaturalNumber())
        {
          if(rfGranularity_ != elementsGranularity)
          {
            NTA_THROW << "Invalid dest dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", a fractional "
              "receptive field size of " <<
              workingParams_.rfSize[i] << " was specified in "
              "combination with a strict mapping with a "
              "granularity of nodes.  Fractional receptive "
              "fields are only valid with strict mappings when "
              "rfGranularity is set to elements.";
          }

          Fraction validityCheck = 
            workingParams_.rfSize[i] * elementCount_;

          if(!validityCheck.isNaturalNumber())
          {
            NTA_THROW << "Invalid dest dimensions " << dims.toString()
                      << " for link " << link_->toString() << ".\n\n"
              "For dimension " << i+1 << ", the specified "
              "receptive field size of "
                      << workingParams_.rfSize[i] << "is invalid since it "
              "would require " << validityCheck << " elements "
              "(given the source region's " << elementCount_ <<
              " elements per node).  Elements cannot be "
              "subdivided, therefore a strict mapping with this"
              " configuration is not possible.";
          }
        }

        // ---
        // If the span for this dimension is zero (indicating no atomic
        // groups of overlapping nodes), then S_i = R_d,i(F_s,i - V_i) + V_i
        // The induced dimension size reduces to:
        //
        // R_s,i = R_d,i * (F_s,i - V_i) + V_i - 2 * H_i
        // ---

        if(workingParams_.span[i].getNumerator() == 0)
        {
          // R_s,i = R_d,i * (F_s,i - V_i) + V_i - 2 * H_i
          Fraction inducedDim = Fraction(dims[i]) *
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]) +
            workingParams_.rfOverlap[i] -
            workingParams_.overhang[i] * 2;

          NTA_CHECK(inducedDim.isNaturalNumber());

          inducedDim.reduce();
          inducedDims.push_back(inducedDim.getNumerator());
        }
        else
        {
          // R_s,i = (R_d,i * S_i * (F_s,i - V_i))/(S_i - V_i) - 2 * H_i
          Fraction inducedDim = (Fraction(dims[i]) *
                                 workingParams_.span[i] *
                                 (workingParams_.rfSize[i] -
                                  workingParams_.rfOverlap[i])) /
            (workingParams_.span[i] -
             workingParams_.rfOverlap[i]) -
            workingParams_.overhang[i] * 2;

          NTA_CHECK(inducedDim.isNaturalNumber());

          inducedDim.reduce();
          inducedDims.push_back(inducedDim.getNumerator());
        }
      }
    }
    else
    {
      // ---
      // Since we are set to non-strict uniformity, we don't need to
      // validate dimensions.  So we'll just calculate the ideal fit using
      // the "strict" formulas.  These will yeild results which are
      // fractions that may not be natural numbers.  When we don't have a
      // valid strict mapping, we want to favor packing in more information
      // than spreading that information out (i.e. if the nearest strict
      // mapping would have had n source nodes per destination node, then
      // we'll favor n + delta source nodes per destination node over
      // n - delta source nodes.  For inducing source dimensions, this
      // implies rounding up.
      // ---

      for(size_t i = 0; i < dims.size(); i++)
      {
        Fraction inducedDim;

        if(workingParams_.span[i].getNumerator() == 0)
        {
          // R_s,i = R_d,i * (F_s,i - V_i) + V_i - 2 * H_i
          inducedDim = Fraction(dims[i]) *
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]) +
            workingParams_.rfOverlap[i] -
            workingParams_.overhang[i] * 2;
        }
        else
        {
          // R_s,i = (R_d,i * S_i * (F_s,i - V_i))/(S_i - V_i) - 2 * H_i
          inducedDim = (Fraction(dims[i]) *
                        workingParams_.span[i] *
                        (workingParams_.rfSize[i] -
                         workingParams_.rfOverlap[i])) /
            (workingParams_.span[i] -
             workingParams_.rfOverlap[i]) -
            workingParams_.overhang[i] * 2;

          Fraction numSpans = (inducedDim +
                               workingParams_.overhang[i] * 2) /
            workingParams_.span[i];

          Fraction nodesPerSpan = Fraction(1) +
            (workingParams_.span[i] -
             workingParams_.rfSize[i]) /
            (workingParams_.rfSize[i] -
             workingParams_.rfOverlap[i]);

          int numWholeSpans = numSpans.getNumerator() / numSpans.getDenominator();

          Fraction properDestDim = Fraction(numWholeSpans) * nodesPerSpan;

          unsigned int properWholeDestDim = properDestDim.getNumerator() /
            properDestDim.getDenominator();

          if(properWholeDestDim != dims[i])
          {
            NTA_WARN << "Since a span was specified, the destination "
              "dimensions are treated such that they are "
              "compatible with the requested span.  In "
              "non-strict mappings, extra source nodes are "
              "divided amongst spans and then distributed as "
              "evenly as possible.  Given the specified "
              "parameters, the destination dimensions being set "
              "will result in " << dims[i] - properWholeDestDim
                     << " destination nodes receiving no input for "
              "dimension " << i+1 << ".";
          }
        }
            
        if(inducedDim.isNaturalNumber())
        {
          inducedDims.push_back(inducedDim.getNumerator() /
                                inducedDim.getDenominator());
        }
        else
        {
          inducedDims.push_back((inducedDim.getNumerator() /
                                 inducedDim.getDenominator()) +
                                1);
        }
      }
    }

    break;
  }
  default:
  {
    NTA_THROW << "UniformLinkPolicy mappings other than 'in' are not yet "
      "implemented.";

    break;
  }
  }

  destDimensions_ = dims;
  srcDimensions_ = inducedDims;
}
  
const Dimensions& UniformLinkPolicy::getSrcDimensions() const
{
  return srcDimensions_;
}

const Dimensions& UniformLinkPolicy::getDestDimensions() const
{
  return destDimensions_;
}

void UniformLinkPolicy::setNodeOutputElementCount(size_t elementCount)
{
  elementCount_ = elementCount;
}

std::pair<Fraction, Fraction>
UniformLinkPolicy::getInputBoundsForNode(Coordinate nodeCoordinate,
                                         size_t dimension) const
{
  NTA_CHECK(isInitialized());

  Fraction lowerIndex(0), upperIndex(0);

  // ---
  // For a mapping of 'in'
  //
  // T_i = the number of destination Nodes per span
  // J_i = the j^th span for dimension i
  //
  // T_i = (S_i - V_i) / (F_s,i - V_i)
  //
  // A given destination Node K is in the j^th span for dimension i given by:
  //
  // J_i = Floor(K_i/T_i)
  //
  // The input for a given destination Node K for dimension i is then the
  // range from:
  //
  // J_i*S_i + (K_i - J_i*T_i)*(F_s,i - V_i) - H_i
  // to
  // J_i*S_i + (F_s,i - 1) + (K_i - J_i*T_i)*(F_s,i - V_i) - H_i
  // ---
  switch(mapping_)
  {
  case inMapping:
  {
    if(strict_)
    {
      Fraction destNodesPerSpan = (workingParams_.span[dimension] -
                                   workingParams_.rfOverlap[dimension]) /
        (workingParams_.rfSize[dimension] -
         workingParams_.rfOverlap[dimension]);

      Fraction nodeInSpanFrac = Fraction(nodeCoordinate[dimension]) /
        destNodesPerSpan;

      size_t nodeInSpan = nodeInSpanFrac.getNumerator() /
        nodeInSpanFrac.getDenominator();

      lowerIndex = workingParams_.span[dimension] *
        nodeInSpan +
        (Fraction(nodeCoordinate[dimension]) -
         destNodesPerSpan *
         nodeInSpan) *
        (workingParams_.rfSize[dimension] -
         workingParams_.rfOverlap[dimension]) -
        workingParams_.overhang[dimension];

      upperIndex = lowerIndex + 
        workingParams_.rfSize[dimension] - Fraction(1);
    }
    else
    {
      // ---
      // Since we're not strict, we will determine our bounds in several
      // steps.  First, we need to calculate the overage over an ideal
      // mapping and spread that overage as evenly as possible across all
      // spans.  Second, we need need to spread the overage in each span
      // as evenly as possible across all receptive fields within that
      // span.
      //
      // If we're working at a granularity level of elements, then
      // fractional results are okay.
      // ---

      Fraction srcNodeOverage = (Fraction(srcDimensions_[dimension]) +
                                 workingParams_.overhang[dimension] * 2) %
        workingParams_.span[dimension];

      Fraction numberOfSpans = (Fraction(srcDimensions_[dimension]) +
                                workingParams_.overhang[dimension] * 2 -
                                srcNodeOverage) /
        workingParams_.span[dimension];

      NTA_CHECK(numberOfSpans.isNaturalNumber());

      Fraction overagePerSpan = srcNodeOverage / numberOfSpans;

      Fraction numRfsPerSpan = (workingParams_.span[dimension] -
                                workingParams_.rfSize[dimension]) /
        (workingParams_.rfSize[dimension] -
         workingParams_.rfOverlap[dimension])
        + 1;

      Fraction effectiveRfSize = workingParams_.rfSize[dimension] +
        (overagePerSpan /
         numRfsPerSpan);

      Fraction effectiveSpan = workingParams_.span[dimension] +
        overagePerSpan;

      Fraction destNodesPerSpan = (workingParams_.span[dimension] -
                                   workingParams_.rfOverlap[dimension]) /
        (workingParams_.rfSize[dimension] -
         workingParams_.rfOverlap[dimension]);

      Fraction nodeInSpanFrac = Fraction(nodeCoordinate[dimension]) /
        destNodesPerSpan;

      size_t nodeInSpan = nodeInSpanFrac.getNumerator() /
        nodeInSpanFrac.getDenominator();

      lowerIndex = effectiveSpan *
        nodeInSpan +
        (Fraction(nodeCoordinate[dimension]) -
         destNodesPerSpan *
         nodeInSpan) *
        (effectiveRfSize -
         workingParams_.rfOverlap[dimension]) -
        workingParams_.overhang[dimension];

      upperIndex = lowerIndex + 
        effectiveRfSize - Fraction(1);

      if(rfGranularity_ == nodesGranularity)
      {
        if(!lowerIndex.isNaturalNumber())
        {
          lowerIndex = Fraction(lowerIndex.getNumerator() /
                                lowerIndex.getDenominator());
        }

        if(!upperIndex.isNaturalNumber())
        {
          upperIndex = Fraction(upperIndex.getNumerator() /
                                upperIndex.getDenominator());
        }
      }
      else
      {
        Fraction wholeElementCheck = lowerIndex * elementCount_;

        if(!wholeElementCheck.isNaturalNumber())
        {
          lowerIndex = Fraction((wholeElementCheck.getNumerator() /
                                 wholeElementCheck.getDenominator())
                                + 1) /
            Fraction(elementCount_);
        }

        wholeElementCheck = upperIndex * elementCount_;

        if(!wholeElementCheck.isNaturalNumber())
        {
          upperIndex = Fraction((wholeElementCheck.getNumerator() /
                                 wholeElementCheck.getDenominator())) /
            Fraction(elementCount_);
        }
      }
    }

    break;
  }
  default:
  {
    NTA_THROW << "UniformLinkPolicy mappings other than 'in' are not yet "
      "implemented.";

    break;
  }
  }

  return std::pair<Fraction, Fraction>(lowerIndex, upperIndex);
}

std::pair<Fraction, Fraction>
UniformLinkPolicy::getInputBoundsForNode(size_t nodeIndex,
                                         size_t dimension) const
{
  NTA_CHECK(isInitialized());

  return getInputBoundsForNode(destDimensions_.getCoordinate(nodeIndex),
                               dimension);
}

void UniformLinkPolicy::getInputForNode(Coordinate nodeCoordinate,
                                        std::vector<size_t>& input) const
{
  // ---
  // We need to get the input bounds for our node in each dimension.
  // The bounds correspond to edges of an orthotope, and the elements
  // contained in the orthotope are the input for the node.
  // ---
  std::vector<std::pair<Fraction, Fraction> > orthotopeBounds;
  orthotopeBounds.reserve(destDimensions_.size());

  for(size_t d = 0; d < destDimensions_.size(); d++)
  {
    // get the bounds (inclusive) in Nodes for this dimension
    std::pair<Fraction, Fraction> dimensionBounds = 
      getInputBoundsForNode(nodeCoordinate,d);

    // convert to an exclusive upper bound
    dimensionBounds.second = dimensionBounds.second + 1;

    orthotopeBounds.push_back(dimensionBounds);
  }

  // ---
  // We now visit each element in the orthotope and populate the input vector
  // with the corresponding element indices; since this is recursive, we
  // create an empty subCoordinate to pass in to the recursive routine
  // ---
  std::vector<Fraction> subCoordinate;
  populateInputElements(input,orthotopeBounds,subCoordinate);
}

void UniformLinkPolicy::getInputForNode(size_t nodeIndex,
                                        std::vector<size_t>& input) const
{
  getInputForNode(destDimensions_.getCoordinate(nodeIndex), input);
}

void UniformLinkPolicy::populateInputElements(
  std::vector<size_t>& input,
  std::vector<std::pair<Fraction,Fraction> > orthotopeBounds,
  std::vector<Fraction>& subCoordinate) const
{
  size_t dimension = orthotopeBounds.size() - subCoordinate.size()- 1;

  // ---
  // When handling element level linking, a Node's elements are treated
  // as if they belonged to each dimension.  For example, a region of size
  // [4, 3] with an elementCount_ of 2 is treated as if its element based
  // size was [8, 6] rather than [8, 3] or [4, 6].  This would seem to imply
  // that there were elementCount_^n elements, when in fact there are not.
  // Visually, one could imagine that the elements are taken from a hypercube
  // with dimensionality equal to elementCount_, but this, again, would
  // primarily put the elements in a favored dimension.  From the above
  // example, you could have element offsets of:
  //
  // [ 0, 1 ]      [ 0, 0 ]
  // [ 0, 1 ]  or  [ 1, 1 ]
  //
  // Rather, we want to take the input elements from the diagonal only.
  //
  // Formally then, when building the splitter map, the input elements are
  // taken from the diagonal of a sparse hypercube having dimensionality
  // equal to the orthotopeBounds, with each dimension being of size
  // elementCount_. Each output element is placed at the hypercube coordinate
  // C such that C_i = E_n for all i where E_n is the element's index within
  // the node.
  //
  // In the case of our two dimensional example, this would be the square of
  // size [2, 2] with element offsets:
  //
  // [ 0, * ]
  // [ *, 1 ]
  //
  // where the asterisks denote null elements.
  //
  // In this example, when processing along either dimension (the first or
  // the second), the first element would be taken from coordinate [1, 1] and
  // the second from [2, 2].
  // ---

  for(Fraction i = orthotopeBounds[dimension].first;
      i < orthotopeBounds[dimension].second;
      i = i+1)
  {
    subCoordinate.insert(subCoordinate.begin(), i);

    if(dimension != 0)
    {
      populateInputElements(input, orthotopeBounds, subCoordinate);
    }
    else
    {
      Coordinate nodeCoordinate;
      std::pair<size_t, size_t> elementOffset =
        std::pair<size_t, size_t>(std::numeric_limits<size_t>::max(),
                                       std::numeric_limits<size_t>::min());

      for(size_t x = 0; x < subCoordinate.size(); x++)
      {
        if(subCoordinate[x].getNumerator() < 0)
        {
          // ---
          // We got a negative number which implies we're in overhang for
          // this dimension.  If our overhang type is null then we won't
          // add any input elements.  If our overhang type is wrap then we
          // need to add elements from the opposite side of the applicable
          // dimension.
          // ---

          switch(workingParams_.overhangType[x])
          {
          case wrapOverhang:
          {
            Fraction effectiveSubCoordinate = Fraction(srcDimensions_[x]) +
              subCoordinate[x];

            nodeCoordinate.push_back(effectiveSubCoordinate.getNumerator() /
                                     effectiveSubCoordinate.getDenominator());

            Fraction fractionalComponent =
              (effectiveSubCoordinate - nodeCoordinate[x]) * elementCount_;

            NTA_CHECK(fractionalComponent.isNaturalNumber());

            size_t fractionalOffset = fractionalComponent.getNumerator() /
              fractionalComponent.getDenominator();

            // ---
            // If a subCoordinate component is at the lower bound for that
            // dimension, then we need to add elements starting at the
            // fractionalOffset and continuing to the elementCount_.
            //
            // Similarly, if the component is at the upper bound for that
            // dimension, then we need to add elements starting at 0 and
            // continuing to the fractionalOffset.
            //
            // Otherwise, we want to add all elements (from 0 to
            // elementCount_).
            //
            // In any case, we want to add as many elements as possible.
            // For example, if we have a fractional overlap at a "corner"
            // of the bounds then we'll overlap only a portion of the
            // elements; whereas if we are at an "edge", then at least one
            // dimension will overlap all of the elements and thus they
            // should all be included.
            // ---
            if(subCoordinate[x] == orthotopeBounds[x].first)
            {
              if(fractionalOffset < elementOffset.first)
              {
                elementOffset.first = fractionalOffset;
              }

              elementOffset.second = elementCount_;
            }
            else if(subCoordinate[x] == orthotopeBounds[x].second)
            {
              elementOffset.first = 0;

              if(fractionalOffset > elementOffset.second)
              {
                elementOffset.second = fractionalOffset;
              }
            }
            else
            {
              elementOffset.first = 0;
              elementOffset.second = elementCount_;
            }

            break;
          }
          case nullOverhang:
          default:
          {
            nodeCoordinate.push_back(0);
            elementOffset = std::pair<size_t, size_t>(0,0);

            break;
          }
          }
        }
        else if(((size_t)
                 (subCoordinate[x].getNumerator() /
                  subCoordinate[x].getDenominator())) > srcDimensions_[x])
        {
          // ---
          // We got a number larger than our source dimension which implies
          // we're in overhang for this dimension.  If our overhang type is
          // null then we won't add any input elements.  If our overhang type
          // is wrap then we need to add elements from the opposite side of
          // the applicable dimension.
          // ---

          switch(workingParams_.overhangType[x])
          {
          case wrapOverhang:
          {
            Fraction effectiveSubCoordinate = subCoordinate[x] -
              Fraction(srcDimensions_[x]);

            nodeCoordinate.push_back(effectiveSubCoordinate.getNumerator() /
                                     effectiveSubCoordinate.getDenominator());

            Fraction fractionalComponent =
              (effectiveSubCoordinate - nodeCoordinate[x]) * elementCount_;

            NTA_CHECK(fractionalComponent.isNaturalNumber());

            size_t fractionalOffset = fractionalComponent.getNumerator() /
              fractionalComponent.getDenominator();

            // ---
            // If a subCoordinate component is at the lower bound for that
            // dimension, then we need to add elements starting at the
            // fractionalOffset and continuing to the elementCount_.
            //
            // Similarly, if the component is at the upper bound for that
            // dimension, then we need to add elements starting at 0 and
            // continuing to the fractionalOffset.
            //
            // Otherwise, we want to add all elements (from 0 to
            // elementCount_).
            //
            // In any case, we want to add as many elements as possible.
            // For example, if we have a fractional overlap at a "corner"
            // of the bounds then we'll overlap only a portion of the
            // elements; whereas if we are at an "edge", then at least one
            // dimension will overlap all of the elements and thus they
            // should all be included.
            // ---
            if(subCoordinate[x] == orthotopeBounds[x].first)
            {
              if(fractionalOffset < elementOffset.first)
              {
                elementOffset.first = fractionalOffset;
              }

              elementOffset.second = elementCount_;
            }
            else if(subCoordinate[x] == orthotopeBounds[x].second)
            {
              elementOffset.first = 0;

              if(fractionalOffset > elementOffset.second)
              {
                elementOffset.second = fractionalOffset;
              }
            }
            else
            {
              elementOffset.first = 0;
              elementOffset.second = elementCount_;
            }

            break;
          }
          case nullOverhang:
          default:
          {
            nodeCoordinate.push_back(0);
            elementOffset = std::pair<size_t, size_t>(0,0);

            break;
          }
          }
        }
        else
        {
          nodeCoordinate.push_back(subCoordinate[x].getNumerator() /
                                   subCoordinate[x].getDenominator());

          Fraction fractionalComponent =
            (subCoordinate[x] - nodeCoordinate[x]) * elementCount_;

          NTA_CHECK(fractionalComponent.isNaturalNumber());

          size_t fractionalOffset = fractionalComponent.getNumerator() /
            fractionalComponent.getDenominator();

          // ---
          // If a subCoordinate component is at the lower bound for that
          // dimension, then we need to add elements starting at the
          // fractionalOffset and continuing to the elementCount_.
          //
          // Similarly, if the component is at the upper bound for that
          // dimension, then we need to add elements starting at 0 and
          // continuing to the fractionalOffset.
          //
          // Otherwise, we want to add all elements (from 0 to
          // elementCount_).
          //
          // In any case, we want to add as many elements as possible.  For
          // example, if we have a fractional overlap at a "corner" of the
          // bounds then we'll overlap only a portion of the elements;
          // whereas if we are at an "edge", then at least one dimension will
          // overlap all of the elements and thus they should all be
          // included.
          // ---
          if(subCoordinate[x] == orthotopeBounds[x].first)
          {
            if(fractionalOffset < elementOffset.first)
            {
              elementOffset.first = fractionalOffset;
            }

            elementOffset.second = elementCount_;
          }
          else if(subCoordinate[x] == orthotopeBounds[x].second)
          {
            elementOffset.first = 0;

            if(fractionalOffset > elementOffset.second)
            {
              elementOffset.second = fractionalOffset;
            }
          }
          else
          {
            elementOffset.first = 0;
            elementOffset.second = elementCount_;
          }
        }
      }

      size_t elementIndex = srcDimensions_.getIndex(nodeCoordinate);
        
      for(size_t x = elementOffset.first; x < elementOffset.second; x++)
      {
        input.push_back(elementIndex * elementCount_ + x);
      }
    }

    subCoordinate.erase(subCoordinate.begin());
  }
}

void UniformLinkPolicy::buildProtoSplitterMap(
  Input::SplitterMap& splitter) const
{
  NTA_CHECK(isInitialized());

  // ---
  // Calculate the number of destination nodes for which we need to create
  // splitter map entries
  // ---
  size_t numDestNodes = 1;
  for(size_t i = 0; i < destDimensions_.size(); i++)
  {
    numDestNodes *= destDimensions_[i];
  }

  NTA_CHECK(splitter.size() == numDestNodes);

  for(size_t i = 0; i < numDestNodes; i++)
  {
    getInputForNode(i, splitter[i]);
  }
}

void UniformLinkPolicy::initialize()
{
  // ---
  // Both Regions now have dimensions, so we will convert spans specified as
  // being equal to zero to the appropriate size.  This simplifies the
  // splitter map calculation since we can work from a single formula.
  // ---

  // ---
  // If our span specification has dimensionality of 1 and a value of 0 (e.g.
  // no span was specified), then we need to promote our workingParams_.span
  // to have the full dimensionality since individual dimensions may vary in
  // size.
  // ---
  if(workingParams_.span.size() == 1 &&
     workingParams_.span[0].getNumerator() == 0)
  {
    for(size_t i = 1; i < srcDimensions_.size(); i++)
    {
      workingParams_.span.push_back(Fraction(0));
    }
  }

  for(size_t i = 0; i < workingParams_.span.size(); i++)
  {
    if(workingParams_.span[i].getNumerator() == 0)
    {
      switch(mapping_)
      {
      case inMapping:
      {
        if(strict_)
        {
          workingParams_.span[i] = Fraction(srcDimensions_[i]) +
            workingParams_.overhang[i] * 2;
        }
        else
        {
          // ---
          // We aren't strict, so we want our span to be the ideal span as
          // if we had qualified as strict (the overage of elements/nodes
          // will be split across receptive fields when calculating node
          // bounds).
          // ---

          workingParams_.span[i] = Fraction(srcDimensions_[i]) -
            ((Fraction(srcDimensions_[i]) +
              workingParams_.overhang[i] * 2 -
              workingParams_.rfSize[i]) %
             (workingParams_.rfSize[i] -
              workingParams_.rfOverlap[i]));
        }

        break;
      }
      case outMapping:
      {
        workingParams_.span[i] = Fraction(destDimensions_[i]) +
          workingParams_.overhang[i] * 2;

        break;
      }
      default:
      {
        break;
      }
      }
    }
  }

  // ---
  // We didn't know the size of the source dimensions at initialization, so
  // we couldn't perform this check in validateParameterConsistency().  Now
  // that we know our dimensions, we'll perform the check.
  // ---
  for(size_t i = 0; i < parameterDimensionality_; i++)
  {
    if(workingParams_.overhang[i] > srcDimensions_[i])
    {
      NTA_THROW << "The overhang can't exceed the size of the source "
        "dimensions";
    }
  }

  initialized_ = true;
}

bool UniformLinkPolicy::isInitialized() const
{
  return initialized_;
}


template <typename T>
UniformLinkPolicy::DefaultValuedVector<T>::DefaultValuedVector()
{};



template <typename T>
T UniformLinkPolicy::DefaultValuedVector<T>::operator[](const size_type index) const
{
  return at(index);
}
    
template <typename T>
T& UniformLinkPolicy::DefaultValuedVector<T>::operator[](const size_type index)
{
  return at(index);
}
    
template <typename T>
T UniformLinkPolicy::DefaultValuedVector<T>::at(const size_type index) const
{
  if(std::vector<T>::size()==1)
  {
    return std::vector<T>::at(0);
  }
  else
  {
    return std::vector<T>::at(index);
  }
}
    
template <typename T>
T& UniformLinkPolicy::DefaultValuedVector<T>::at(const size_type index)
{
  if(std::vector<T>::size()==1)
  {
    return std::vector<T>::at(0);
  }
  else
  {
    return std::vector<T>::at(index);
  }
}

template struct nta::UniformLinkPolicy::DefaultValuedVector<Fraction>;
template struct nta::UniformLinkPolicy::DefaultValuedVector<nta::UniformLinkPolicy::OverhangType>;

}

