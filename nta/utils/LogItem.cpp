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
* LogItem implementation
*/


#include <nta/utils/LogItem.hpp>
#include <nta/types/Exception.hpp>
#include <iostream>  // cout
#include <stdexcept> // runtime_error

using namespace nta;

std::ostream* LogItem::ostream_ = nullptr;

void LogItem::setOutputFile(std::ostream& ostream)
{
  ostream_ = &ostream;
}

LogItem::LogItem(const char *filename, int line, LogLevel level)
  : filename_(filename), lineno_(line), level_(level), msg_("") 
{}

LogItem::~LogItem()
{
  std::string slevel;
  switch(level_)
  {
  case debug:
    slevel = "DEBUG:";
    break;
  case warn:
    slevel = "WARN: ";
    break;
  case info:
    slevel = "INFO: ";
    break;
  case error:
    slevel = "ERROR:";
    break;
  default:
    slevel = "Unknown: ";
    break;
  }


  if (ostream_ == nullptr)
    ostream_ = &(std::cout);

  (*ostream_) << slevel << "  " << msg_.str();
  if (level_ == error)
    (*ostream_) << " [" << filename_ << " line " << lineno_ << "]";
  (*ostream_) << std::endl;

}

std::ostringstream& LogItem::stream() {
  return msg_;
}


