#ifndef NTA_PYTHON_STREAM_HPP
#define NTA_PYTHON_STREAM_HPP

#ifdef NTA_PYTHON_SUPPORT

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

#include <py_support/PyHelpers.hpp>
#include <iosfwd>
#include <sstream>

///////////////////////////////////////////////////////////////////
/// Provides a stream that outputs a PyString on class close()
///
/// @b Responsibility
/// Must make a PyString object that contains the same string as
/// was passed to the ostream returned by getStream()
///
/// @b Description
/// After instantiation, a call to getStream() returns an ostream
/// that collects the characters fed to it. Any subsequent call
/// to close() will return a PyObject * to a PyString that 
/// contains the current contents of the ostream.
/// 
/// @note
/// A close() before a getStream() will return an empty PyString.
/// 
///////////////////////////////////////////////////////////////////
class SharedPythonOStream
{
public:
  SharedPythonOStream(size_t maxSize);
  std::ostream &getStream();
  PyObject *close();

private:
	size_t target_size_;
	std::stringstream ss_;
};

//------------------------------------------------------------------

#endif // NTA_PYTHON_SUPPORT

#endif // NTA_PYTHON_STREAM_HPP





