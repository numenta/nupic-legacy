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
* Implementation for VectorFileSensor class
*/

#include <nta/engine/Region.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/regions/VectorFileSensor.hpp>
#include <nta/utils/Log.hpp>
#include <nta/utils/StringUtils.hpp>
//#include <nta/os/FStream.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <stdexcept>
#include <string>
#include <iostream>
#include <sstream>
#include <list>
#include <cstring> // strlen

using namespace std;
namespace nta
{

//----------------------------------------------------------------------------

VectorFileSensor::VectorFileSensor(const ValueMap& params, Region* region) :
  RegionImpl(region),
  
  repeatCount_(1),
  iterations_(0),
  curVector_(0),
  activeOutputCount_(0),
  hasCategoryOut_(false),
  hasResetOut_(false),
  dataOut_(NTA_BasicType_Real32),
  categoryOut_(NTA_BasicType_Real32),
  resetOut_(NTA_BasicType_Real32),
  filename_(""),
  scalingMode_("none"),
  recentFile_("")
{
  activeOutputCount_ = params.getScalar("activeOutputCount")->getValue<NTA_UInt32>();
  if (params.contains("hasCategoryOut"))
    hasCategoryOut_ =
      params.getScalar("hasCategoryOut")->getValue<NTA_UInt32>() == 1;
  if (params.contains("hasResetOut"))
    hasResetOut_ =
      params.getScalar("hasResetOut")->getValue<NTA_UInt32>() == 1;
  if (params.contains("inputFile"))
    filename_ = *params.getString("inputFile");
  if (params.contains("repeatCount"))
    repeatCount_ = params.getScalar("repeatCount")->getValue<NTA_UInt32>();
}

VectorFileSensor::VectorFileSensor(BundleIO& bundle, Region* region) :
  RegionImpl(region),
  repeatCount_(1),
  iterations_(0),
  curVector_(0),
  activeOutputCount_(0),
  hasCategoryOut_(false),
  hasResetOut_(false),
  dataOut_(NTA_BasicType_Real32),
  categoryOut_(NTA_BasicType_Real32),
  resetOut_(NTA_BasicType_Real32),
  filename_(""),
  scalingMode_("none"),
  recentFile_("")
{
  deserialize(bundle);
}

void VectorFileSensor::initialize()
{
  NTA_CHECK(region_ != nullptr);
  dataOut_ = region_->getOutputData("dataOut");
  categoryOut_ = region_->getOutputData("categoryOut");
  resetOut_ = region_->getOutputData("resetOut");

  if (dataOut_.getCount() != activeOutputCount_)
  {
    NTA_THROW
      << "VectorFileSensor::init - wrong output size: " << dataOut_.getCount()
      << " should be: " << activeOutputCount_;
  }
}

VectorFileSensor::~VectorFileSensor()
{
}

//----------------------------------------------------------------------------

void VectorFileSensor::compute()
{
  // It's not necessarily an error to have no outputs. In this case we just return
  if (dataOut_.getCount() == 0) 
    return;
  
  // Don't write if there is no open file. 
  if (recentFile_ == "")
  {
    NTA_WARN << "VectorFileSesnsor compute() called, but there is no open file";
    return;
  }   

  NTA_CHECK(vectorFile_.vectorCount() > 0)
    << "VectorFileSensor::compute - no data vectors in memory."
    << "Perhaps no data file has been loaded using the 'loadFile'"
    << " execute command.";
  
  if (iterations_ % repeatCount_ == 0) {
    // Get index to next vector and copy scaled vector to our output
    curVector_++;
    curVector_ %= vectorFile_.vectorCount();
  }
  
  Real *out = (Real *) dataOut_.getBuffer();

  Size count = dataOut_.getCount();
  UInt offset = 0;  
  
  if (hasCategoryOut_)
  {
    Real * categoryOut = (Real32 *) categoryOut_.getBuffer();
    vectorFile_.getRawVector((nta::UInt)curVector_, categoryOut, offset, 1);
    offset++;
  }
  
  if (hasResetOut_)
  {
    Real * resetOut = (Real32 *)resetOut_.getBuffer();
    vectorFile_.getRawVector((nta::UInt)curVector_, resetOut, offset, 1);
    offset++;
  }
  
  vectorFile_.getScaledVector((nta::UInt)curVector_, out, offset, count);
  iterations_++;
}

//--------------------------------------------------------------------------------
inline const char *checkExtensions(const std::string &filename, 
    const char *const *extensions)
{
  while(*extensions) {
    const char *ext = *extensions;
    if(filename.rfind(ext) == (filename.size() - ::strlen(ext)))
      return ext;

    ++extensions;
  }
  return nullptr;
}

//--------------------------------------------------------------------------------
/// Execute a VectorFilesensor specific command
std::string VectorFileSensor::executeCommand(const std::vector<std::string>& args, Int64 index)
                       
{
  UInt32 argCount = args.size();
  // Get the first argument (command string)
  NTA_CHECK(argCount > 0) << "VectorFileSensor: No command name";
  string command = args[0];

  // Process each command
  if ((command == "loadFile") || (command == "appendFile")) 
  {
    NTA_CHECK(argCount > 1) << "VectorFileSensor: no filename specified for " << command;

    UInt32 labeled = 2;  // Default format is 2

    // string filename = ReadStringFromBuffer(*buf2);
    string filename(args[1]);
    cout << "In VectorFileSensor " << filename << endl;

    if (argCount == 3)
    {
      labeled = StringUtils::toUInt32(args[2]);
    }
    else 
    {
      // Check for some common extensions.
      const char *csvExtensions[] = { ".csv", ".CSV", nullptr };
      if(checkExtensions(filename, csvExtensions)) 
      {
        cout << "Reading CSV file" << endl;
        labeled = 3; // CSV format.
      }
    }

    // Detect binary file format and set labeled flag to read little endian
    // binary file
    if (filename.substr(filename.size() - 3, 3) == "bin") {
      cout << "Reading binary file" << endl;
      labeled = 4;
    }
    
    if (labeled > (UInt32) VectorFile::maxFormat())
      NTA_THROW << "VectorFileSensor: unknown file format '" << labeled << "'";

    // Read in new set of vectors
    // If the command is loadFile, we clear the list first and reset the position 
    // to the beginning
    if (command == "loadFile") 
      vectorFile_.clear(false);

    //Timer t(true);

    UInt32 elementCount = activeOutputCount_;
    if (hasCategoryOut_)
      elementCount ++;
    if (hasResetOut_)
      elementCount ++;

    vectorFile_.appendFile(filename, elementCount, labeled);
    cout << "Read " << vectorFile_.vectorCount() << " vectors" << endl;
    //in " << t.getValue() << " seconds" << endl;

    if (command == "loadFile") 
      seek(0);

    recentFile_ = filename;
  }

  else if (command == "dump") 
  {
    nta::Byte message[256];
    Size n = ::sprintf(message,
      "VectorFileSensor isLabeled = %d repeatCount = %d vectorCount = %d iterations = %d\n",
      vectorFile_.isLabeled(), (int) repeatCount_, (int) vectorFile_.vectorCount(), (int) iterations_);
    //out.write(message, n);
    return string(message, n);
  }

  else if (command == "saveFile")
  {
    NTA_CHECK(argCount > 1) << "VectorFileSensor: no filename specified for " << command;

    Int32 format = 2;  // Default format is 2
    Int64 begin = 0, end = 0;
    bool hasEnd = false;

    string filename(args[1]);

    if (argCount > 2)
    {
      format = StringUtils::toUInt32(args[2]);
      if ((format < 0) || (format > VectorFile::maxFormat()))
        NTA_THROW << "VectorFileSensor: unknown file format '" << format << "'";
    }

    if (argCount > 3)
    {
      begin = StringUtils::toUInt32(args[3]);
    }

    if (argCount > 4)
    {
      end = StringUtils::toUInt32(args[4]);
      hasEnd = true;
    }

    NTA_CHECK(argCount <= 5) << "VectorFileSensor: too many arguments";


    OFStream f(filename.c_str());
    if (hasEnd)
      vectorFile_.saveVectors(f, dataOut_.getCount(), format, begin, end);
    else
      vectorFile_.saveVectors(f, dataOut_.getCount(), format, begin, end);
  }

  else 
  {
    NTA_THROW << "VectorFileSensor: Unknown execute command: '" << command << "' sent!";
  }

  return "";
} 

//--------------------------------------------------------------------------------

void VectorFileSensor::setParameterFromBuffer(const std::string& name, 
                                              Int64 index, 
                                              IReadBuffer& value)
{
  const char* where = "VectorFileSensor, while setting parameter: ";

  UInt32 int_param = 0;

  if (name == "repeatCount") 
  {
    NTA_CHECK(value.read(int_param) == 0)
      << where << "Unable to read repeatCount: " 
      << int_param << " - Should be a positive integer";

    if (int_param >= 1) 
    {
      repeatCount_ = int_param;
    }
  }

  else if (name == "position") 
  {
    NTA_CHECK(value.read(int_param) == 0)
      << where << "Unable to read position: " 
      << int_param << " - Should be a positive integer";
    if ( int_param < vectorFile_.vectorCount() ) 
    {
      seek(int_param);
    }
    else 
    {
      NTA_THROW << "VectorFileSensor: invalid position "
        << " to seek to: " << int_param;
    }
  }

  else if (name == "scalingMode") 
  {
    // string mode = ReadStringFromvaluefer(value);
    string mode(value.getData(), value.getSize());
    if (mode == "none") vectorFile_.resetScaling();
    else if (mode == "standardForm") vectorFile_.setStandardScaling();
    else if (mode != "custom") // Do nothing if set to custom
      NTA_THROW << where << " Unknown scaling mode: " << mode;
    scalingMode_ = mode;
  }
  
  else if (name == "hasCategoryOut") {
    NTA_CHECK(value.read(int_param) == 0)
      << where << "Unable to read hasCategoryOut: " 
      << int_param << " - Should be a positive integer";
    
    hasCategoryOut_ = int_param == 1;
  }  

  else if (name == "hasResetOut") {
    NTA_CHECK(value.read(int_param) == 0)
      << where << "Unable to read hasResetOut: " 
      << int_param << " - Should be a positive integer";
    
    hasResetOut_ = int_param == 1;
  }  
  
  else 
  {
    NTA_THROW << where << "couldn't set '" << name << "'";
  }

}

//--------------------------------------------------------------------------------
void VectorFileSensor::getParameterFromBuffer(const std::string& name, 
                                              Int64 index, 
                                              IWriteBuffer& value)
{
  const char* where = "VectorFileSensor, while getting parameter: ";

  Int32 res = 0;

  if (name == "vectorCount") {
    res = value.write((UInt32)vectorFile_.vectorCount());
  }

  else if (name == "position") {
    res = value.write(UInt32(curVector_+1));
  }  

  else if (name == "repeatCount") {
    res = value.write(UInt32(repeatCount_));
  }  

  else if (name == "scalingMode") {
    // res = value.writeString(scalingMode_.data(), (Size)scalingMode_.size());
    res = value.write(scalingMode_.data(), (Size)scalingMode_.size());
  }  

  else if (name == "recentFile") {
    // res = value.writeString(recentFile_.data(), (Size)recentFile_.size());
    if (recentFile_.empty())
    {
      res = value.write("", 1);
    }
    else
    {
      res = value.write(recentFile_.data(), (Size)recentFile_.size());
    }
  }  

  else if (name == "scaleVector") {
    stringstream buf;
    Real s = 0, o = 0;
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.getScaling(i, s, o);
      buf << s << " ";
    }
    string bufstr = buf.str();
    res = value.write(bufstr.c_str(), (Size)bufstr.size());
  }

  else if (name == "activeOutputCount") {
    res = value.write(UInt32(activeOutputCount_));
  }  

  else if (name == "maxOutputVectorCount") {
    res = value.write(UInt32(vectorFile_.vectorCount() * repeatCount_));
  }  

  else if (name == "offsetVector") {
    stringstream buf;
    Real s = 0, o = 0;
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.getScaling(i, s, o);
      buf << o << " ";
    }
    string bufstr = buf.str();
    res = value.write(bufstr.c_str(), (Size)bufstr.size());
  }

  else if (name == "hasCategoryOut") {
    res = value.write(UInt32(hasCategoryOut_));
  }  

  else if (name == "hasResetOut") {
    res = value.write(UInt32(hasResetOut_));
  }  

  NTA_CHECK(res >= 0) << where << "couldn't retrieve '" << name << "'";
}

//----------------------------------------------------------------------
void VectorFileSensor::seek(int n) 
{
  NTA_CHECK( (n >= 0) && ((unsigned int) n < vectorFile_.vectorCount()) );

  // Set curVector_ to be one before the vector we want and reset iterations
  iterations_ = 0;
  curVector_ = n - 1;
  //circular-buffer, reached one end of vector/line, continue fro the other
  if (n - 1 <= 0) curVector_ = (NTA_Size)vectorFile_.vectorCount() - 1;
}

size_t VectorFileSensor::getNodeOutputElementCount(const std::string& outputName)
{
  NTA_CHECK(outputName == "dataOut") << "Invalid output name: " << outputName;
  return activeOutputCount_;
}

void VectorFileSensor::serialize(BundleIO& bundle)
{  
  std::ofstream & f = bundle.getOutputStream("vfs");
  f << repeatCount_ << " "
    << activeOutputCount_ << " "
    << filename_ << " "
    << scalingMode_ << " ";
  f.close();
}

void VectorFileSensor::deserialize(BundleIO& bundle)
{
  std::ifstream& f = bundle.getInputStream("vfs");
  f >> repeatCount_
    >> activeOutputCount_
    >> filename_
    >> scalingMode_;
  f.close();
}

Spec* VectorFileSensor::createSpec()
{
  auto  ns = new Spec;
  ns->description = 
  "VectorFileSensor is a basic sensor for reading files containing vectors.\n"
  "\n"
  "VectorFileSensor reads in a text file containing lists of numbers\n"
  "and outputs these vectors in sequence. The output is updated\n"
  "each time the sensor's compute() method is called. If\n"
  "repeatCount is > 1, then each vector is repeated that many times\n"
  "before moving to the next one. The sensor loops when the end of\n"
  "the vector list is reached. The default file format\n"
  "is as follows (assuming the sensor is configured with N outputs):\n"
  "\n"
  "  e11 e12 e13 ... e1N\n"
  "  e21 e22 e23 ... e2N\n"
  "    : \n"
  "  eM1 eM2 eM3 ... eMN\n"
  "\n"
  "In this format the sensor ignores all whitespace in the file, including newlines\n"
  "If the file contains an incorrect number of floats, the sensor has no way\n"
  "of checking and will silently ignore the extra numbers at the end of the file.\n"
  "\n"
  "The sensor can also read in comma-separated (CSV) files following the format:\n"
  "\n"
  "  e11, e12, e13, ... ,e1N\n"
  "  e21, e22, e23, ... ,e2N\n"
  "    : \n"
  "  eM1, eM2, eM3, ... ,eMN\n"
  "\n"
  "When reading CSV files the sensor expects that each line contains a new vector\n"
  "Any line containing too few elements or any text will be ignored. If there are\n"
  "more than N numbers on a line, the sensor retains only the first N.\n";
  
  ns->outputs.add(
    "dataOut",
    OutputSpec("Data read from file", 
      NTA_BasicType_Real32, 
      0, // count
      true, // isRegionLevel
      true   // isDefaultOutput
      ));


  ns->outputs.add(
    "categoryOut",
    OutputSpec("The current category encoded as a float (represent a whole number)", 
      NTA_BasicType_Real32, 
      1, // count
      true, // isRegionLevel
      false   // isDefaultOutput
      ));

  ns->outputs.add(
    "resetOut",
    OutputSpec("Sequence reset signal: 0 - do nothing, otherwise start a new sequence", 
      NTA_BasicType_Real32, 
      1, // count
      true, // isRegionLevel
      false   // isDefaultOutput
      ));

  ns->parameters.add(
    "vectorCount",
    ParameterSpec(
      "The number of vectors currently loaded in memory.", 
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "interval: [0, ...]", // constraints
      "0", // defaultValue
      ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "position",
    ParameterSpec(
      "Set or get the current position within the list of vectors in memory.", 
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "interval: [0, ...]", // constraints
      "0", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "repeatCount",
    ParameterSpec(
     "Set or get the current repeatCount. Each vector is repeated\n"
     "repeatCount times before moving to the next one.",
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "interval: [1, ...]", // constraints
      "1", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "recentFile",
    ParameterSpec(
      "Writes output vectors to this file on each compute. Will append to any\n"
      "existing data in the file. This parameter must be set at runtime before\n"
      "the first compute is called. Throws an exception if it is not set or\n"
      "the file cannot be written to.\n", 
      NTA_BasicType_Byte, 
      0,  // elementCount
      "", // constraints
      "", // defaultValue
      ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "scalingMode",
    ParameterSpec(
      "During compute, each vector is adjusted as follows. If X is the data vector,\n"
      "S the scaling vector and O the offset vector, then the node's output\n"
      "                Y[i] = S[i]*(X[i] + O[i]).\n"
      "\n"
      "Scaling is applied according to scalingMode as follows:\n"
      "\n"
      "    If 'none', the vectors are unchanged, i.e. S[i]=1 and O[i]=0.\n"
      "    If 'standardForm', S[i] is 1/standard deviation(i) and O[i] = - mean(i)\n"
      "    If 'custom', each component is adjusted according to the vectors specified by the\n"
      "setScale and setOffset commands.\n", 
      NTA_BasicType_Byte, 
      0,  // elementCount
      "", // constraints
      "none", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "scaleVector",
    ParameterSpec(
      "Set or return the current scale vector S.\n", 
      NTA_BasicType_Real32, 
      0,  // elementCount
      "", // constraints
      "", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "offsetVector",
    ParameterSpec(
      "Set or return the current offset vector 0.\n",
      NTA_BasicType_Real32, 
      0,  // elementCount
      "", // constraints
      "", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "activeOutputCount",
    ParameterSpec(
      "The number of active outputs of the node.",
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "interval: [0, ...]", // constraints
      "", // default Value
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "maxOutputVectorCount",
    ParameterSpec(
      "The number of output vectors that can be generated by this sensor\n"
      "under the current configuration.", 
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "interval: [0, ...]", // constraints
      "0", // defaultValue
      ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "hasCategoryOut",
    ParameterSpec(
      "Category info is present in data file.", 
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "enum: [0, 1]", // constraints
      "0", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "hasResetOut",
    ParameterSpec(
      "New sequence reset signal is present in data file.",
      NTA_BasicType_UInt32, 
      1,  // elementCount
      "enum: [0, 1]", // constraints
      "0", // defaultValue
      ParameterSpec::ReadWriteAccess
      ));

  ns->commands.add(
    "loadFile", 
    CommandSpec(
      "loadFile <filename> [file_format]\n"
      "Reads vectors from the specified file, replacing any vectors\n"
      "currently in the list. Position is set to zero. \n"
      "Available file formats are: \n"
      "       0        # Reads in unlabeled file with first number = element count\n"
      "       1        # Reads in a labeled file with first number = element count (deprecated)\n"
      "       2        # Reads in unlabeled file without element count (default)\n"
      "       3        # Reads in a csv file\n"
     ));

  ns->commands.add(
    "appendFile",
    CommandSpec(
      "appendFile <filename> [file_format]\n"
      "Reads vectors from the specified file, appending to current vector list.\n"
      "Position remains unchanged. Available file formats are: \n"
      "       0        # Reads in unlabeled file with first number = element count\n"
      "       1        # Reads in a labeled file with first number = element count (deprecated)\n"
      "       2        # Reads in unlabeled file without element count (default)\n"
      "       3        # Reads in a csv file\n"));

  ns->commands.add(
    "saveFile",
    CommandSpec(
      "saveFile filename [format [begin [end]]]\n"
      "Save the currently loaded vectors to a file. Typically used for debugging\n"
      "but may be used to convert between formats.\n"));

  ns->commands.add("dump", CommandSpec("Displays some debugging info."));





  return ns;
}


void VectorFileSensor::getParameterArray(const std::string& name, Int64 index, Array & a)
{
  if (a.getCount() != dataOut_.getCount())
    NTA_THROW << "getParameterArray(), array size is: " << a.getCount() << "instead of : " << dataOut_.getCount();

  Real * buf = (Real *)a.getBuffer();
  Real dummy;
  if (name == "scaleVector")
  {
    Real * buf = (Real *)a.getBuffer();
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.getScaling(i, buf[i], dummy);
    }
  }
  else if (name == "offsetVector")
  {
    
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.getScaling(i, dummy, buf[i]);
    }
  }
  else
  {
    NTA_THROW << "VectorfileSensor::getParameterArray(), unknown parameter: " << name;
  }
}

void VectorFileSensor::setParameterArray(const std::string& name, Int64 index, const Array & a)
{
  if (a.getCount() != dataOut_.getCount())
    NTA_THROW << "setParameterArray(), array size is: " << a.getCount() << "instead of : " << dataOut_.getCount();

  Real * buf = (Real *)a.getBuffer();
  if (name == "scaleVector")
  {
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.setScale(i, buf[i]);
    }
  }
  else if (name == "offsetVector")
  {
    
    for (UInt i = 0; i < vectorFile_.getElementCount(); i++)
    {
      vectorFile_.setOffset(i, buf[i]);
    }
  }
  else
  {
    NTA_THROW << "VectorfileSensor::setParameterArray(), unknown parameter: " << name;
  }

  scalingMode_ = "custom";
}

size_t VectorFileSensor::getParameterArrayCount(const std::string& name, Int64 index)
{
  if (name != "scaleVector" && name != "offsetVector")
    NTA_THROW << "VectorFileSensor::getParameterArrayCount(), unknown array parameter: " << name;

  return dataOut_.getCount();
}


} // end namespace nta

