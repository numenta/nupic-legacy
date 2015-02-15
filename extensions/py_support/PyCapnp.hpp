/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

// This file contains utility functions for converting from pycapnp schema to
// compiled in schema. It requires linking to both libcapnp and libcapnpc.

#ifndef NTA_PY_CAPNP_HPP
#define NTA_PY_CAPNP_HPP

#include <Python.h>

#include <capnp/any.h>
#include <capnp/dynamic.h>
#include <capnp/message.h>
#include <capnp/schema-parser.h>

namespace nupic
{

  struct pycapnp_SchemaParser {
    PyObject_HEAD
    void *__pyx_vtab;
     ::capnp::SchemaParser *thisptr;
    PyObject *modules_by_id;
  };

  struct pycapnp_DynamicStructBuilder {
    PyObject_HEAD
    void *__pyx_vtab;
     ::capnp::DynamicStruct::Builder thisptr;
    PyObject *_parent;
    int is_root;
    int _is_written;
    PyObject *_schema;
  };

  struct pycapnp_DynamicStructReader {
    PyObject_HEAD
    void *__pyx_vtab;
     ::capnp::DynamicStruct::Reader thisptr;
    PyObject *_parent;
    int is_root;
    PyObject *_obj_to_pin;
    PyObject *_schema;
  };

  template<class T>
  typename T::Builder getBuilder(PyObject* pyBuilder)
  {
    PyObject* capnpModule = PyImport_AddModule("capnp.lib.capnp");
    PyObject* pySchemaParser = PyObject_GetAttrString(capnpModule,
                                                      "_global_schema_parser");
    pycapnp_SchemaParser* schemaParser = (pycapnp_SchemaParser*)pySchemaParser;
    schemaParser->thisptr->loadCompiledTypeAndDependencies<T>();

    pycapnp_DynamicStructBuilder* dynamicStruct =
        (pycapnp_DynamicStructBuilder*)pyBuilder;
    capnp::DynamicStruct::Builder& builder = dynamicStruct->thisptr;
    typename T::Builder proto = builder.as<T>();
    return proto;
  }

  template<class T>
  typename T::Reader getReader(PyObject* pyReader)
  {
    PyObject* capnpModule = PyImport_AddModule("capnp.lib.capnp");
    PyObject* pySchemaParser = PyObject_GetAttrString(capnpModule,
                                                      "_global_schema_parser");
    pycapnp_SchemaParser* schemaParser = (pycapnp_SchemaParser*)pySchemaParser;
    schemaParser->thisptr->loadCompiledTypeAndDependencies<T>();

    pycapnp_DynamicStructReader* dynamicStruct =
        (pycapnp_DynamicStructReader*)pyReader;
    capnp::DynamicStruct::Reader& reader = dynamicStruct->thisptr;
    typename T::Reader proto = reader.as<T>();
    return proto;
  }

}  // namespace nupic

#endif  // NTA_PY_CAPNP_HPP
