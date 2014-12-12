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

#include <py_support/PythonStream.hpp>
#include <nupic/utils/Log.hpp>

/**
 * Bumps up size to a nicely aligned larger size.
 * Taken for NuPIC2 from PythonUtils.hpp
 */
static size_t NextPythonSize(size_t n)
{
  n += 1;
  n += 8 - (n % 8);
  return n;
}

// -------------------------------------------------------------
SharedPythonOStream::SharedPythonOStream(size_t maxSize) :
	target_size_(NextPythonSize(maxSize)),
	ss_(std::ios_base::out)
{
}

// -------------------------------------------------------------
std::ostream &SharedPythonOStream::getStream()
{
	return ss_;
}

// -------------------------------------------------------------
PyObject * SharedPythonOStream::close()
{
	ss_.flush();

	if (ss_.str().length() > target_size_)
    throw std::runtime_error("Stream output larger than allocated buffer.");

  return PyString_FromStringAndSize(ss_.str().c_str(), ss_.str().length());
}

#endif // NTA_PYTHON_SUPPORT


