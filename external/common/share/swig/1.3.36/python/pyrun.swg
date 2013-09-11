/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * pyrun.swg
 *
 * This file contains the runtime support for Python modules
 * and includes code for managing global variables and pointer
 * type checking.
 *
 * ----------------------------------------------------------------------------- */

/* Common SWIG API */

/* for raw pointers */
#define SWIG_Python_ConvertPtr(obj, pptr, type, flags)  SWIG_Python_ConvertPtrAndOwn(obj, pptr, type, flags, 0)
#define SWIG_ConvertPtr(obj, pptr, type, flags)         SWIG_Python_ConvertPtr(obj, pptr, type, flags)
#define SWIG_ConvertPtrAndOwn(obj,pptr,type,flags,own)  SWIG_Python_ConvertPtrAndOwn(obj, pptr, type, flags, own)
#define SWIG_NewPointerObj(ptr, type, flags)            SWIG_Python_NewPointerObj(ptr, type, flags)
#define SWIG_CheckImplicit(ty)                          SWIG_Python_CheckImplicit(ty) 
#define SWIG_AcquirePtr(ptr, src)                       SWIG_Python_AcquirePtr(ptr, src)
#define swig_owntype                                    int

/* for raw packed data */
#define SWIG_ConvertPacked(obj, ptr, sz, ty)            SWIG_Python_ConvertPacked(obj, ptr, sz, ty)
#define SWIG_NewPackedObj(ptr, sz, type)                SWIG_Python_NewPackedObj(ptr, sz, type)

/* for class or struct pointers */
#define SWIG_ConvertInstance(obj, pptr, type, flags)    SWIG_ConvertPtr(obj, pptr, type, flags)
#define SWIG_NewInstanceObj(ptr, type, flags)           SWIG_NewPointerObj(ptr, type, flags)

/* for C or C++ function pointers */
#define SWIG_ConvertFunctionPtr(obj, pptr, type)        SWIG_Python_ConvertFunctionPtr(obj, pptr, type)
#define SWIG_NewFunctionPtrObj(ptr, type)               SWIG_Python_NewPointerObj(ptr, type, 0)

/* for C++ member pointers, ie, member methods */
#define SWIG_ConvertMember(obj, ptr, sz, ty)            SWIG_Python_ConvertPacked(obj, ptr, sz, ty)
#define SWIG_NewMemberObj(ptr, sz, type)                SWIG_Python_NewPackedObj(ptr, sz, type)


/* Runtime API */

#define SWIG_GetModule(clientdata)                      SWIG_Python_GetModule()
#define SWIG_SetModule(clientdata, pointer)             SWIG_Python_SetModule(pointer)
#define SWIG_NewClientData(obj)                         PySwigClientData_New(obj)

#define SWIG_SetErrorObj                                SWIG_Python_SetErrorObj                            
#define SWIG_SetErrorMsg                        	SWIG_Python_SetErrorMsg				   
#define SWIG_ErrorType(code)                    	SWIG_Python_ErrorType(code)                        
#define SWIG_Error(code, msg)            		SWIG_Python_SetErrorMsg(SWIG_ErrorType(code), msg) 
#define SWIG_fail                        		goto fail					   


/* Runtime API implementation */

/* Error manipulation */

SWIGINTERN void 
SWIG_Python_SetErrorObj(PyObject *errtype, PyObject *obj) {
  SWIG_PYTHON_THREAD_BEGIN_BLOCK; 
  PyErr_SetObject(errtype, obj);
  Py_DECREF(obj);
  SWIG_PYTHON_THREAD_END_BLOCK;
}

SWIGINTERN void 
SWIG_Python_SetErrorMsg(PyObject *errtype, const char *msg) {
  SWIG_PYTHON_THREAD_BEGIN_BLOCK;
  PyErr_SetString(errtype, (char *) msg);
  SWIG_PYTHON_THREAD_END_BLOCK;
}

#define SWIG_Python_Raise(obj, type, desc)  SWIG_Python_SetErrorObj(SWIG_Python_ExceptionType(desc), obj)

/* Set a constant value */

SWIGINTERN void
SWIG_Python_SetConstant(PyObject *d, const char *name, PyObject *obj) {   
  PyDict_SetItemString(d, (char*) name, obj);
  Py_DECREF(obj);                            
}

/* Append a value to the result obj */

SWIGINTERN PyObject*
SWIG_Python_AppendOutput(PyObject* result, PyObject* obj) {
#if !defined(SWIG_PYTHON_OUTPUT_TUPLE)
  if (!result) {
    result = obj;
  } else if (result == Py_None) {
    Py_DECREF(result);
    result = obj;
  } else {
    if (!PyList_Check(result)) {
      PyObject *o2 = result;
      result = PyList_New(1);
      PyList_SetItem(result, 0, o2);
    }
    PyList_Append(result,obj);
    Py_DECREF(obj);
  }
  return result;
#else
  PyObject*   o2;
  PyObject*   o3;
  if (!result) {
    result = obj;
  } else if (result == Py_None) {
    Py_DECREF(result);
    result = obj;
  } else {
    if (!PyTuple_Check(result)) {
      o2 = result;
      result = PyTuple_New(1);
      PyTuple_SET_ITEM(result, 0, o2);
    }
    o3 = PyTuple_New(1);
    PyTuple_SET_ITEM(o3, 0, obj);
    o2 = result;
    result = PySequence_Concat(o2, o3);
    Py_DECREF(o2);
    Py_DECREF(o3);
  }
  return result;
#endif
}

/* Unpack the argument tuple */

SWIGINTERN int
SWIG_Python_UnpackTuple(PyObject *args, const char *name, Py_ssize_t min, Py_ssize_t max, PyObject **objs)
{
  if (!args) {
    if (!min && !max) {
      return 1;
    } else {
      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got none", 
		   name, (min == max ? "" : "at least "), (int)min);
      return 0;
    }
  }  
  if (!PyTuple_Check(args)) {
    PyErr_SetString(PyExc_SystemError, "UnpackTuple() argument list is not a tuple");
    return 0;
  } else {
    register Py_ssize_t l = PyTuple_GET_SIZE(args);
    if (l < min) {
      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got %d", 
		   name, (min == max ? "" : "at least "), (int)min, (int)l);
      return 0;
    } else if (l > max) {
      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got %d", 
		   name, (min == max ? "" : "at most "), (int)max, (int)l);
      return 0;
    } else {
      register int i;
      for (i = 0; i < l; ++i) {
	objs[i] = PyTuple_GET_ITEM(args, i);
      }
      for (; l < max; ++l) {
	objs[l] = 0;
      }
      return i + 1;
    }    
  }
}

/* A functor is a function object with one single object argument */
#if PY_VERSION_HEX >= 0x02020000
#define SWIG_Python_CallFunctor(functor, obj)	        PyObject_CallFunctionObjArgs(functor, obj, NULL);
#else
#define SWIG_Python_CallFunctor(functor, obj)	        PyObject_CallFunction(functor, "O", obj);
#endif

/*
  Helper for static pointer initialization for both C and C++ code, for example
  static PyObject *SWIG_STATIC_POINTER(MyVar) = NewSomething(...);
*/
#ifdef __cplusplus
#define SWIG_STATIC_POINTER(var)  var
#else
#define SWIG_STATIC_POINTER(var)  var = 0; if (!var) var
#endif

/* -----------------------------------------------------------------------------
 * Pointer declarations
 * ----------------------------------------------------------------------------- */

/* Flags for new pointer objects */
#define SWIG_POINTER_NOSHADOW       (SWIG_POINTER_OWN      << 1)
#define SWIG_POINTER_NEW            (SWIG_POINTER_NOSHADOW | SWIG_POINTER_OWN)

#define SWIG_POINTER_IMPLICIT_CONV  (SWIG_POINTER_DISOWN   << 1)

#ifdef __cplusplus
extern "C" {
#if 0
} /* cc-mode */
#endif
#endif

/*  How to access Py_None */
#if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__)
#  ifndef SWIG_PYTHON_NO_BUILD_NONE
#    ifndef SWIG_PYTHON_BUILD_NONE
#      define SWIG_PYTHON_BUILD_NONE
#    endif
#  endif
#endif

#ifdef SWIG_PYTHON_BUILD_NONE
#  ifdef Py_None
#   undef Py_None
#   define Py_None SWIG_Py_None()
#  endif
SWIGRUNTIMEINLINE PyObject * 
_SWIG_Py_None(void)
{
  PyObject *none = Py_BuildValue((char*)"");
  Py_DECREF(none);
  return none;
}
SWIGRUNTIME PyObject * 
SWIG_Py_None(void)
{
  static PyObject *SWIG_STATIC_POINTER(none) = _SWIG_Py_None();
  return none;
}
#endif

/* The python void return value */

SWIGRUNTIMEINLINE PyObject * 
SWIG_Py_Void(void)
{
  PyObject *none = Py_None;
  Py_INCREF(none);
  return none;
}

/* PySwigClientData */

typedef struct {
  PyObject *klass;
  PyObject *newraw;
  PyObject *newargs;
  PyObject *destroy;
  int delargs;
  int implicitconv;
} PySwigClientData;

SWIGRUNTIMEINLINE int 
SWIG_Python_CheckImplicit(swig_type_info *ty)
{
  PySwigClientData *data = (PySwigClientData *)ty->clientdata;
  return data ? data->implicitconv : 0;
}

SWIGRUNTIMEINLINE PyObject *
SWIG_Python_ExceptionType(swig_type_info *desc) {
  PySwigClientData *data = desc ? (PySwigClientData *) desc->clientdata : 0;
  PyObject *klass = data ? data->klass : 0;
  return (klass ? klass : PyExc_RuntimeError);
}


SWIGRUNTIME PySwigClientData * 
PySwigClientData_New(PyObject* obj)
{
  if (!obj) {
    return 0;
  } else {
    PySwigClientData *data = (PySwigClientData *)malloc(sizeof(PySwigClientData));
    /* the klass element */
    data->klass = obj;
    Py_INCREF(data->klass);
    /* the newraw method and newargs arguments used to create a new raw instance */
    if (PyClass_Check(obj)) {
      data->newraw = 0;
      data->newargs = obj;
      Py_INCREF(obj);
    } else {
#if (PY_VERSION_HEX < 0x02020000)
      data->newraw = 0;
#else
      data->newraw = PyObject_GetAttrString(data->klass, (char *)"__new__");
#endif
      if (data->newraw) {
	Py_INCREF(data->newraw);
	data->newargs = PyTuple_New(1);
	PyTuple_SetItem(data->newargs, 0, obj);
      } else {
	data->newargs = obj;
      }
      Py_INCREF(data->newargs);
    }
    /* the destroy method, aka as the C++ delete method */
    data->destroy = PyObject_GetAttrString(data->klass, (char *)"__swig_destroy__");
    if (PyErr_Occurred()) {
      PyErr_Clear();
      data->destroy = 0;
    }
    if (data->destroy) {
      int flags;
      Py_INCREF(data->destroy);
      flags = PyCFunction_GET_FLAGS(data->destroy);
#ifdef METH_O
      data->delargs = !(flags & (METH_O));
#else
      data->delargs = 0;
#endif
    } else {
      data->delargs = 0;
    }
    data->implicitconv = 0;
    return data;
  }
}

SWIGRUNTIME void 
PySwigClientData_Del(PySwigClientData* data)
{
  Py_XDECREF(data->newraw);
  Py_XDECREF(data->newargs);
  Py_XDECREF(data->destroy);
}

/* =============== PySwigObject =====================*/

typedef struct {
  PyObject_HEAD
  void *ptr;
  swig_type_info *ty;
  int own;
  PyObject *next;
} PySwigObject;

SWIGRUNTIME PyObject *
PySwigObject_long(PySwigObject *v)
{
  return PyLong_FromVoidPtr(v->ptr);
}

SWIGRUNTIME PyObject *
PySwigObject_format(const char* fmt, PySwigObject *v)
{
  PyObject *res = NULL;
  PyObject *args = PyTuple_New(1);
  if (args) {
    if (PyTuple_SetItem(args, 0, PySwigObject_long(v)) == 0) {
      PyObject *ofmt = PyString_FromString(fmt);
      if (ofmt) {
	res = PyString_Format(ofmt,args);
	Py_DECREF(ofmt);
      }
      Py_DECREF(args);
    }
  }
  return res;
}

SWIGRUNTIME PyObject *
PySwigObject_oct(PySwigObject *v)
{
  return PySwigObject_format("%o",v);
}

SWIGRUNTIME PyObject *
PySwigObject_hex(PySwigObject *v)
{
  return PySwigObject_format("%x",v);
}

SWIGRUNTIME PyObject *
#ifdef METH_NOARGS
PySwigObject_repr(PySwigObject *v)
#else
PySwigObject_repr(PySwigObject *v, PyObject *args)
#endif
{
  const char *name = SWIG_TypePrettyName(v->ty);
  PyObject *hex = PySwigObject_hex(v);    
  PyObject *repr = PyString_FromFormat("<Swig Object of type '%s' at 0x%s>", name, PyString_AsString(hex));
  Py_DECREF(hex);
  if (v->next) {
#ifdef METH_NOARGS
    PyObject *nrep = PySwigObject_repr((PySwigObject *)v->next);
#else
    PyObject *nrep = PySwigObject_repr((PySwigObject *)v->next, args);
#endif
    PyString_ConcatAndDel(&repr,nrep);
  }
  return repr;  
}

SWIGRUNTIME int
PySwigObject_print(PySwigObject *v, FILE *fp, int SWIGUNUSEDPARM(flags))
{
#ifdef METH_NOARGS
  PyObject *repr = PySwigObject_repr(v);
#else
  PyObject *repr = PySwigObject_repr(v, NULL);
#endif
  if (repr) {
    fputs(PyString_AsString(repr), fp);
    Py_DECREF(repr);
    return 0; 
  } else {
    return 1; 
  }
}

SWIGRUNTIME PyObject *
PySwigObject_str(PySwigObject *v)
{
  char result[SWIG_BUFFER_SIZE];
  return SWIG_PackVoidPtr(result, v->ptr, v->ty->name, sizeof(result)) ?
    PyString_FromString(result) : 0;
}

SWIGRUNTIME int
PySwigObject_compare(PySwigObject *v, PySwigObject *w)
{
  void *i = v->ptr;
  void *j = w->ptr;
  return (i < j) ? -1 : ((i > j) ? 1 : 0);
}

SWIGRUNTIME PyTypeObject* _PySwigObject_type(void);

SWIGRUNTIME PyTypeObject*
PySwigObject_type(void) {
  static PyTypeObject *SWIG_STATIC_POINTER(type) = _PySwigObject_type();
  return type;
}

SWIGRUNTIMEINLINE int
PySwigObject_Check(PyObject *op) {
  return ((op)->ob_type == PySwigObject_type())
    || (strcmp((op)->ob_type->tp_name,"PySwigObject") == 0);
}

SWIGRUNTIME PyObject *
PySwigObject_New(void *ptr, swig_type_info *ty, int own);

SWIGRUNTIME void
PySwigObject_dealloc(PyObject *v)
{
  PySwigObject *sobj = (PySwigObject *) v;
  PyObject *next = sobj->next;
  if (sobj->own == SWIG_POINTER_OWN) {
    swig_type_info *ty = sobj->ty;
    PySwigClientData *data = ty ? (PySwigClientData *) ty->clientdata : 0;
    PyObject *destroy = data ? data->destroy : 0;
    if (destroy) {
      /* destroy is always a VARARGS method */
      PyObject *res;
      if (data->delargs) {
	/* we need to create a temporal object to carry the destroy operation */
	PyObject *tmp = PySwigObject_New(sobj->ptr, ty, 0);
	res = SWIG_Python_CallFunctor(destroy, tmp);
	Py_DECREF(tmp);
      } else {
	PyCFunction meth = PyCFunction_GET_FUNCTION(destroy);
	PyObject *mself = PyCFunction_GET_SELF(destroy);
	res = ((*meth)(mself, v));
      }
      Py_XDECREF(res);
    } 
#if !defined(SWIG_PYTHON_SILENT_MEMLEAK)
    else {
      const char *name = SWIG_TypePrettyName(ty);
      printf("swig/python detected a memory leak of type '%s', no destructor found.\n", (name ? name : "unknown"));
    }
#endif
  } 
  Py_XDECREF(next);
  PyObject_DEL(v);
}

SWIGRUNTIME PyObject* 
PySwigObject_append(PyObject* v, PyObject* next)
{
  PySwigObject *sobj = (PySwigObject *) v;
#ifndef METH_O
  PyObject *tmp = 0;
  if (!PyArg_ParseTuple(next,(char *)"O:append", &tmp)) return NULL;
  next = tmp;
#endif
  if (!PySwigObject_Check(next)) {
    return NULL;
  }
  sobj->next = next;
  Py_INCREF(next);
  return SWIG_Py_Void();
}

SWIGRUNTIME PyObject* 
#ifdef METH_NOARGS
PySwigObject_next(PyObject* v)
#else
PySwigObject_next(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
#endif
{
  PySwigObject *sobj = (PySwigObject *) v;
  if (sobj->next) {    
    Py_INCREF(sobj->next);
    return sobj->next;
  } else {
    return SWIG_Py_Void();
  }
}

SWIGINTERN PyObject*
#ifdef METH_NOARGS
PySwigObject_disown(PyObject *v)
#else
PySwigObject_disown(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
#endif
{
  PySwigObject *sobj = (PySwigObject *)v;
  sobj->own = 0;
  return SWIG_Py_Void();
}

SWIGINTERN PyObject*
#ifdef METH_NOARGS
PySwigObject_acquire(PyObject *v)
#else
PySwigObject_acquire(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
#endif
{
  PySwigObject *sobj = (PySwigObject *)v;
  sobj->own = SWIG_POINTER_OWN;
  return SWIG_Py_Void();
}

SWIGINTERN PyObject*
PySwigObject_own(PyObject *v, PyObject *args)
{
  PyObject *val = 0;
#if (PY_VERSION_HEX < 0x02020000)
  if (!PyArg_ParseTuple(args,(char *)"|O:own",&val))
#else
  if (!PyArg_UnpackTuple(args, (char *)"own", 0, 1, &val)) 
#endif
    {
      return NULL;
    } 
  else
    {
      PySwigObject *sobj = (PySwigObject *)v;
      PyObject *obj = PyBool_FromLong(sobj->own);
      if (val) {
#ifdef METH_NOARGS
	if (PyObject_IsTrue(val)) {
	  PySwigObject_acquire(v);
	} else {
	  PySwigObject_disown(v);
	}
#else
	if (PyObject_IsTrue(val)) {
	  PySwigObject_acquire(v,args);
	} else {
	  PySwigObject_disown(v,args);
	}
#endif
      } 
      return obj;
    }
}

#ifdef METH_O
static PyMethodDef
swigobject_methods[] = {
  {(char *)"disown",  (PyCFunction)PySwigObject_disown,  METH_NOARGS,  (char *)"releases ownership of the pointer"},
  {(char *)"acquire", (PyCFunction)PySwigObject_acquire, METH_NOARGS,  (char *)"aquires ownership of the pointer"},
  {(char *)"own",     (PyCFunction)PySwigObject_own,     METH_VARARGS, (char *)"returns/sets ownership of the pointer"},
  {(char *)"append",  (PyCFunction)PySwigObject_append,  METH_O,       (char *)"appends another 'this' object"},
  {(char *)"next",    (PyCFunction)PySwigObject_next,    METH_NOARGS,  (char *)"returns the next 'this' object"},
  {(char *)"__repr__",(PyCFunction)PySwigObject_repr,    METH_NOARGS,  (char *)"returns object representation"},
  {0, 0, 0, 0}  
};
#else
static PyMethodDef
swigobject_methods[] = {
  {(char *)"disown",  (PyCFunction)PySwigObject_disown,  METH_VARARGS,  (char *)"releases ownership of the pointer"},
  {(char *)"acquire", (PyCFunction)PySwigObject_acquire, METH_VARARGS,  (char *)"aquires ownership of the pointer"},
  {(char *)"own",     (PyCFunction)PySwigObject_own,     METH_VARARGS,  (char *)"returns/sets ownership of the pointer"},
  {(char *)"append",  (PyCFunction)PySwigObject_append,  METH_VARARGS,  (char *)"appends another 'this' object"},
  {(char *)"next",    (PyCFunction)PySwigObject_next,    METH_VARARGS,  (char *)"returns the next 'this' object"},
  {(char *)"__repr__",(PyCFunction)PySwigObject_repr,   METH_VARARGS,  (char *)"returns object representation"},
  {0, 0, 0, 0}  
};
#endif

#if PY_VERSION_HEX < 0x02020000
SWIGINTERN PyObject *
PySwigObject_getattr(PySwigObject *sobj,char *name)
{
  return Py_FindMethod(swigobject_methods, (PyObject *)sobj, name);
}
#endif

SWIGRUNTIME PyTypeObject*
_PySwigObject_type(void) {
  static char swigobject_doc[] = "Swig object carries a C/C++ instance pointer";
  
  static PyNumberMethods PySwigObject_as_number = {
    (binaryfunc)0, /*nb_add*/
    (binaryfunc)0, /*nb_subtract*/
    (binaryfunc)0, /*nb_multiply*/
    (binaryfunc)0, /*nb_divide*/
    (binaryfunc)0, /*nb_remainder*/
    (binaryfunc)0, /*nb_divmod*/
    (ternaryfunc)0,/*nb_power*/
    (unaryfunc)0,  /*nb_negative*/
    (unaryfunc)0,  /*nb_positive*/
    (unaryfunc)0,  /*nb_absolute*/
    (inquiry)0,    /*nb_nonzero*/
    0,		   /*nb_invert*/
    0,		   /*nb_lshift*/
    0,		   /*nb_rshift*/
    0,		   /*nb_and*/
    0,		   /*nb_xor*/
    0,		   /*nb_or*/
    (coercion)0,   /*nb_coerce*/
    (unaryfunc)PySwigObject_long, /*nb_int*/
    (unaryfunc)PySwigObject_long, /*nb_long*/
    (unaryfunc)0,                 /*nb_float*/
    (unaryfunc)PySwigObject_oct,  /*nb_oct*/
    (unaryfunc)PySwigObject_hex,  /*nb_hex*/
#if PY_VERSION_HEX >= 0x02050000 /* 2.5.0 */
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 /* nb_inplace_add -> nb_index */
#elif PY_VERSION_HEX >= 0x02020000 /* 2.2.0 */
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 /* nb_inplace_add -> nb_inplace_true_divide */
#elif PY_VERSION_HEX >= 0x02000000 /* 2.0.0 */
    0,0,0,0,0,0,0,0,0,0,0 /* nb_inplace_add -> nb_inplace_or */
#endif
  };

  static PyTypeObject pyswigobject_type;  
  static int type_init = 0;
  if (!type_init) {
    const PyTypeObject tmp
      = {
	PyObject_HEAD_INIT(NULL)
	0,				    /* ob_size */
	(char *)"PySwigObject",		    /* tp_name */
	sizeof(PySwigObject),		    /* tp_basicsize */
	0,			            /* tp_itemsize */
	(destructor)PySwigObject_dealloc,   /* tp_dealloc */
	(printfunc)PySwigObject_print,	    /* tp_print */
#if PY_VERSION_HEX < 0x02020000
	(getattrfunc)PySwigObject_getattr,  /* tp_getattr */ 
#else
	(getattrfunc)0,			    /* tp_getattr */ 
#endif
	(setattrfunc)0,			    /* tp_setattr */ 
	(cmpfunc)PySwigObject_compare,	    /* tp_compare */ 
	(reprfunc)PySwigObject_repr,	    /* tp_repr */    
	&PySwigObject_as_number,	    /* tp_as_number */
	0,				    /* tp_as_sequence */
	0,				    /* tp_as_mapping */
	(hashfunc)0,			    /* tp_hash */
	(ternaryfunc)0,			    /* tp_call */
	(reprfunc)PySwigObject_str,	    /* tp_str */
	PyObject_GenericGetAttr,            /* tp_getattro */
	0,				    /* tp_setattro */
	0,		                    /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT,	            /* tp_flags */
	swigobject_doc, 	            /* tp_doc */        
	0,                                  /* tp_traverse */
	0,                                  /* tp_clear */
	0,                                  /* tp_richcompare */
	0,                                  /* tp_weaklistoffset */
#if PY_VERSION_HEX >= 0x02020000
	0,                                  /* tp_iter */
	0,                                  /* tp_iternext */
	swigobject_methods,		    /* tp_methods */ 
	0,			            /* tp_members */
	0,				    /* tp_getset */	    	
	0,			            /* tp_base */	        
	0,				    /* tp_dict */	    	
	0,				    /* tp_descr_get */  	
	0,				    /* tp_descr_set */  	
	0,				    /* tp_dictoffset */ 	
	0,				    /* tp_init */	    	
	0,				    /* tp_alloc */	    	
	0,			            /* tp_new */	    	
	0,	                            /* tp_free */	   
        0,                                  /* tp_is_gc */  
	0,				    /* tp_bases */   
	0,				    /* tp_mro */
	0,				    /* tp_cache */   
 	0,				    /* tp_subclasses */
	0,				    /* tp_weaklist */
#endif
#if PY_VERSION_HEX >= 0x02030000
	0,                                  /* tp_del */
#endif
#ifdef COUNT_ALLOCS
	0,0,0,0                             /* tp_alloc -> tp_next */
#endif
      };
    pyswigobject_type = tmp;
    pyswigobject_type.ob_type = &PyType_Type;
    type_init = 1;
  }
  return &pyswigobject_type;
}

SWIGRUNTIME PyObject *
PySwigObject_New(void *ptr, swig_type_info *ty, int own)
{
  PySwigObject *sobj = PyObject_NEW(PySwigObject, PySwigObject_type());
  if (sobj) {
    sobj->ptr  = ptr;
    sobj->ty   = ty;
    sobj->own  = own;
    sobj->next = 0;
  }
  return (PyObject *)sobj;
}

/* -----------------------------------------------------------------------------
 * Implements a simple Swig Packed type, and use it instead of string
 * ----------------------------------------------------------------------------- */

typedef struct {
  PyObject_HEAD
  void *pack;
  swig_type_info *ty;
  size_t size;
} PySwigPacked;

SWIGRUNTIME int
PySwigPacked_print(PySwigPacked *v, FILE *fp, int SWIGUNUSEDPARM(flags))
{
  char result[SWIG_BUFFER_SIZE];
  fputs("<Swig Packed ", fp); 
  if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))) {
    fputs("at ", fp); 
    fputs(result, fp); 
  }
  fputs(v->ty->name,fp); 
  fputs(">", fp);
  return 0; 
}
  
SWIGRUNTIME PyObject *
PySwigPacked_repr(PySwigPacked *v)
{
  char result[SWIG_BUFFER_SIZE];
  if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))) {
    return PyString_FromFormat("<Swig Packed at %s%s>", result, v->ty->name);
  } else {
    return PyString_FromFormat("<Swig Packed %s>", v->ty->name);
  }  
}

SWIGRUNTIME PyObject *
PySwigPacked_str(PySwigPacked *v)
{
  char result[SWIG_BUFFER_SIZE];
  if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))){
    return PyString_FromFormat("%s%s", result, v->ty->name);
  } else {
    return PyString_FromString(v->ty->name);
  }  
}

SWIGRUNTIME int
PySwigPacked_compare(PySwigPacked *v, PySwigPacked *w)
{
  size_t i = v->size;
  size_t j = w->size;
  int s = (i < j) ? -1 : ((i > j) ? 1 : 0);
  return s ? s : strncmp((char *)v->pack, (char *)w->pack, 2*v->size);
}

SWIGRUNTIME PyTypeObject* _PySwigPacked_type(void);

SWIGRUNTIME PyTypeObject*
PySwigPacked_type(void) {
  static PyTypeObject *SWIG_STATIC_POINTER(type) = _PySwigPacked_type();
  return type;
}

SWIGRUNTIMEINLINE int
PySwigPacked_Check(PyObject *op) {
  return ((op)->ob_type == _PySwigPacked_type()) 
    || (strcmp((op)->ob_type->tp_name,"PySwigPacked") == 0);
}

SWIGRUNTIME void
PySwigPacked_dealloc(PyObject *v)
{
  if (PySwigPacked_Check(v)) {
    PySwigPacked *sobj = (PySwigPacked *) v;
    free(sobj->pack);
  }
  PyObject_DEL(v);
}

SWIGRUNTIME PyTypeObject*
_PySwigPacked_type(void) {
  static char swigpacked_doc[] = "Swig object carries a C/C++ instance pointer";
  static PyTypeObject pyswigpacked_type;
  static int type_init = 0;  
  if (!type_init) {
    const PyTypeObject tmp
      = {
	PyObject_HEAD_INIT(NULL)
	0,				    /* ob_size */	
	(char *)"PySwigPacked",		    /* tp_name */	
	sizeof(PySwigPacked),		    /* tp_basicsize */	
	0,				    /* tp_itemsize */	
	(destructor)PySwigPacked_dealloc,   /* tp_dealloc */	
	(printfunc)PySwigPacked_print,	    /* tp_print */   	
	(getattrfunc)0,			    /* tp_getattr */ 	
	(setattrfunc)0,			    /* tp_setattr */ 	
	(cmpfunc)PySwigPacked_compare,	    /* tp_compare */ 	
	(reprfunc)PySwigPacked_repr,	    /* tp_repr */    	
	0,	                            /* tp_as_number */	
	0,				    /* tp_as_sequence */
	0,				    /* tp_as_mapping */	
	(hashfunc)0,			    /* tp_hash */	
	(ternaryfunc)0,			    /* tp_call */	
	(reprfunc)PySwigPacked_str,	    /* tp_str */	
	PyObject_GenericGetAttr,            /* tp_getattro */
	0,				    /* tp_setattro */
	0,		                    /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT,	            /* tp_flags */
	swigpacked_doc, 	            /* tp_doc */
	0,                                  /* tp_traverse */
	0,                                  /* tp_clear */
	0,                                  /* tp_richcompare */
	0,                                  /* tp_weaklistoffset */
#if PY_VERSION_HEX >= 0x02020000
	0,                                  /* tp_iter */
	0,                                  /* tp_iternext */
	0,		                    /* tp_methods */ 
	0,			            /* tp_members */
	0,				    /* tp_getset */	    	
	0,			            /* tp_base */	        
	0,				    /* tp_dict */	    	
	0,				    /* tp_descr_get */  	
	0,				    /* tp_descr_set */  	
	0,				    /* tp_dictoffset */ 	
	0,				    /* tp_init */	    	
	0,				    /* tp_alloc */	    	
	0,			            /* tp_new */	    	
	0, 	                            /* tp_free */	   
        0,                                  /* tp_is_gc */  
	0,				    /* tp_bases */   
	0,				    /* tp_mro */
	0,				    /* tp_cache */   
 	0,				    /* tp_subclasses */
	0,				    /* tp_weaklist */
#endif
#if PY_VERSION_HEX >= 0x02030000
	0,                                  /* tp_del */
#endif
#ifdef COUNT_ALLOCS
	0,0,0,0                             /* tp_alloc -> tp_next */
#endif
      };
    pyswigpacked_type = tmp;
    pyswigpacked_type.ob_type = &PyType_Type;
    type_init = 1;
  }
  return &pyswigpacked_type;
}

SWIGRUNTIME PyObject *
PySwigPacked_New(void *ptr, size_t size, swig_type_info *ty)
{
  PySwigPacked *sobj = PyObject_NEW(PySwigPacked, PySwigPacked_type());
  if (sobj) {
    void *pack = malloc(size);
    if (pack) {
      memcpy(pack, ptr, size);
      sobj->pack = pack;
      sobj->ty   = ty;
      sobj->size = size;
    } else {
      PyObject_DEL((PyObject *) sobj);
      sobj = 0;
    }
  }
  return (PyObject *) sobj;
}

SWIGRUNTIME swig_type_info *
PySwigPacked_UnpackData(PyObject *obj, void *ptr, size_t size)
{
  if (PySwigPacked_Check(obj)) {
    PySwigPacked *sobj = (PySwigPacked *)obj;
    if (sobj->size != size) return 0;
    memcpy(ptr, sobj->pack, size);
    return sobj->ty;
  } else {
    return 0;
  }
}

/* -----------------------------------------------------------------------------
 * pointers/data manipulation
 * ----------------------------------------------------------------------------- */

SWIGRUNTIMEINLINE PyObject *
_SWIG_This(void)
{
  return PyString_FromString("this");
}

SWIGRUNTIME PyObject *
SWIG_This(void)
{
  static PyObject *SWIG_STATIC_POINTER(swig_this) = _SWIG_This();
  return swig_this;
}

/* #define SWIG_PYTHON_SLOW_GETSET_THIS */

SWIGRUNTIME PySwigObject *
SWIG_Python_GetSwigThis(PyObject *pyobj) 
{
  if (PySwigObject_Check(pyobj)) {
    return (PySwigObject *) pyobj;
  } else {
    PyObject *obj = 0;
#if (!defined(SWIG_PYTHON_SLOW_GETSET_THIS) && (PY_VERSION_HEX >= 0x02030000))
    if (PyInstance_Check(pyobj)) {
      obj = _PyInstance_Lookup(pyobj, SWIG_This());      
    } else {
      PyObject **dictptr = _PyObject_GetDictPtr(pyobj);
      if (dictptr != NULL) {
	PyObject *dict = *dictptr;
	obj = dict ? PyDict_GetItem(dict, SWIG_This()) : 0;
      } else {
#ifdef PyWeakref_CheckProxy
	if (PyWeakref_CheckProxy(pyobj)) {
	  PyObject *wobj = PyWeakref_GET_OBJECT(pyobj);
	  return wobj ? SWIG_Python_GetSwigThis(wobj) : 0;
	}
#endif
	obj = PyObject_GetAttr(pyobj,SWIG_This());
	if (obj) {
	  Py_DECREF(obj);
	} else {
	  if (PyErr_Occurred()) PyErr_Clear();
	  return 0;
	}
      }
    }
#else
    obj = PyObject_GetAttr(pyobj,SWIG_This());
    if (obj) {
      Py_DECREF(obj);
    } else {
      if (PyErr_Occurred()) PyErr_Clear();
      return 0;
    }
#endif
    if (obj && !PySwigObject_Check(obj)) {
      /* a PyObject is called 'this', try to get the 'real this'
	 PySwigObject from it */ 
      return SWIG_Python_GetSwigThis(obj);
    }
    return (PySwigObject *)obj;
  }
}

/* Acquire a pointer value */

SWIGRUNTIME int
SWIG_Python_AcquirePtr(PyObject *obj, int own) {
  if (own == SWIG_POINTER_OWN) {
    PySwigObject *sobj = SWIG_Python_GetSwigThis(obj);
    if (sobj) {
      int oldown = sobj->own;
      sobj->own = own;
      return oldown;
    }
  }
  return 0;
}

/* Convert a pointer value */

SWIGRUNTIME int
SWIG_Python_ConvertPtrAndOwn(PyObject *obj, void **ptr, swig_type_info *ty, int flags, int *own) {
  if (!obj) return SWIG_ERROR;
  if (obj == Py_None) {
    if (ptr) *ptr = 0;
    return SWIG_OK;
  } else {
    PySwigObject *sobj = SWIG_Python_GetSwigThis(obj);
    if (own)
      *own = 0;
    while (sobj) {
      void *vptr = sobj->ptr;
      if (ty) {
	swig_type_info *to = sobj->ty;
	if (to == ty) {
	  /* no type cast needed */
	  if (ptr) *ptr = vptr;
	  break;
	} else {
	  swig_cast_info *tc = SWIG_TypeCheck(to->name,ty);
	  if (!tc) {
	    sobj = (PySwigObject *)sobj->next;
	  } else {
	    if (ptr) {
              int newmemory = 0;
              *ptr = SWIG_TypeCast(tc,vptr,&newmemory);
              if (newmemory == SWIG_CAST_NEW_MEMORY) {
                assert(own);
                if (own)
                  *own = *own | SWIG_CAST_NEW_MEMORY;
              }
            }
	    break;
	  }
	}
      } else {
	if (ptr) *ptr = vptr;
	break;
      }
    }
    if (sobj) {
      if (own)
        *own = *own | sobj->own;
      if (flags & SWIG_POINTER_DISOWN) {
	sobj->own = 0;
      }
      return SWIG_OK;
    } else {
      int res = SWIG_ERROR;
      if (flags & SWIG_POINTER_IMPLICIT_CONV) {
	PySwigClientData *data = ty ? (PySwigClientData *) ty->clientdata : 0;
	if (data && !data->implicitconv) {
	  PyObject *klass = data->klass;
	  if (klass) {
	    PyObject *impconv;
	    data->implicitconv = 1; /* avoid recursion and call 'explicit' constructors*/
	    impconv = SWIG_Python_CallFunctor(klass, obj);
	    data->implicitconv = 0;
	    if (PyErr_Occurred()) {
	      PyErr_Clear();
	      impconv = 0;
	    }
	    if (impconv) {
	      PySwigObject *iobj = SWIG_Python_GetSwigThis(impconv);
	      if (iobj) {
		void *vptr;
		res = SWIG_Python_ConvertPtrAndOwn((PyObject*)iobj, &vptr, ty, 0, 0);
		if (SWIG_IsOK(res)) {
		  if (ptr) {
		    *ptr = vptr;
		    /* transfer the ownership to 'ptr' */
		    iobj->own = 0;
		    res = SWIG_AddCast(res);
		    res = SWIG_AddNewMask(res);
		  } else {
		    res = SWIG_AddCast(res);		    
		  }
		}
	      }
	      Py_DECREF(impconv);
	    }
	  }
	}
      }
      return res;
    }
  }
}

/* Convert a function ptr value */

SWIGRUNTIME int
SWIG_Python_ConvertFunctionPtr(PyObject *obj, void **ptr, swig_type_info *ty) {
  if (!PyCFunction_Check(obj)) {
    return SWIG_ConvertPtr(obj, ptr, ty, 0);
  } else {
    void *vptr = 0;
    
    /* here we get the method pointer for callbacks */
    const char *doc = (((PyCFunctionObject *)obj) -> m_ml -> ml_doc);
    const char *desc = doc ? strstr(doc, "swig_ptr: ") : 0;
    if (desc) {
      desc = ty ? SWIG_UnpackVoidPtr(desc + 10, &vptr, ty->name) : 0;
      if (!desc) return SWIG_ERROR;
    }
    if (ty) {
      swig_cast_info *tc = SWIG_TypeCheck(desc,ty);
      if (tc) {
        int newmemory = 0;
        *ptr = SWIG_TypeCast(tc,vptr,&newmemory);
        assert(!newmemory); /* newmemory handling not yet implemented */
      } else {
        return SWIG_ERROR;
      }
    } else {
      *ptr = vptr;
    }
    return SWIG_OK;
  }
}

/* Convert a packed value value */

SWIGRUNTIME int
SWIG_Python_ConvertPacked(PyObject *obj, void *ptr, size_t sz, swig_type_info *ty) {
  swig_type_info *to = PySwigPacked_UnpackData(obj, ptr, sz);
  if (!to) return SWIG_ERROR;
  if (ty) {
    if (to != ty) {
      /* check type cast? */
      swig_cast_info *tc = SWIG_TypeCheck(to->name,ty);
      if (!tc) return SWIG_ERROR;
    }
  }
  return SWIG_OK;
}  

/* -----------------------------------------------------------------------------
 * Create a new pointer object
 * ----------------------------------------------------------------------------- */

/*
  Create a new instance object, whitout calling __init__, and set the
  'this' attribute.
*/

SWIGRUNTIME PyObject* 
SWIG_Python_NewShadowInstance(PySwigClientData *data, PyObject *swig_this)
{
#if (PY_VERSION_HEX >= 0x02020000)
  PyObject *inst = 0;
  PyObject *newraw = data->newraw;
  if (newraw) {
    inst = PyObject_Call(newraw, data->newargs, NULL);
    if (inst) {
#if !defined(SWIG_PYTHON_SLOW_GETSET_THIS)
      PyObject **dictptr = _PyObject_GetDictPtr(inst);
      if (dictptr != NULL) {
	PyObject *dict = *dictptr;
	if (dict == NULL) {
	  dict = PyDict_New();
	  *dictptr = dict;
	  PyDict_SetItem(dict, SWIG_This(), swig_this);
	}
      }
#else
      PyObject *key = SWIG_This();
      PyObject_SetAttr(inst, key, swig_this);
#endif
    }
  } else {
    PyObject *dict = PyDict_New();
    PyDict_SetItem(dict, SWIG_This(), swig_this);
    inst = PyInstance_NewRaw(data->newargs, dict);
    Py_DECREF(dict);
  }
  return inst;
#else
#if (PY_VERSION_HEX >= 0x02010000)
  PyObject *inst;
  PyObject *dict = PyDict_New();
  PyDict_SetItem(dict, SWIG_This(), swig_this);
  inst = PyInstance_NewRaw(data->newargs, dict);
  Py_DECREF(dict);
  return (PyObject *) inst;
#else
  PyInstanceObject *inst = PyObject_NEW(PyInstanceObject, &PyInstance_Type);
  if (inst == NULL) {
    return NULL;
  }
  inst->in_class = (PyClassObject *)data->newargs;
  Py_INCREF(inst->in_class);
  inst->in_dict = PyDict_New();
  if (inst->in_dict == NULL) {
    Py_DECREF(inst);
    return NULL;
  }
#ifdef Py_TPFLAGS_HAVE_WEAKREFS
  inst->in_weakreflist = NULL;
#endif
#ifdef Py_TPFLAGS_GC
  PyObject_GC_Init(inst);
#endif
  PyDict_SetItem(inst->in_dict, SWIG_This(), swig_this);
  return (PyObject *) inst;
#endif
#endif
}

SWIGRUNTIME void
SWIG_Python_SetSwigThis(PyObject *inst, PyObject *swig_this)
{
 PyObject *dict;
#if (PY_VERSION_HEX >= 0x02020000) && !defined(SWIG_PYTHON_SLOW_GETSET_THIS)
 PyObject **dictptr = _PyObject_GetDictPtr(inst);
 if (dictptr != NULL) {
   dict = *dictptr;
   if (dict == NULL) {
     dict = PyDict_New();
     *dictptr = dict;
   }
   PyDict_SetItem(dict, SWIG_This(), swig_this);
   return;
 }
#endif
 dict = PyObject_GetAttrString(inst, (char*)"__dict__");
 PyDict_SetItem(dict, SWIG_This(), swig_this);
 Py_DECREF(dict);
} 


SWIGINTERN PyObject *
SWIG_Python_InitShadowInstance(PyObject *args) {
  PyObject *obj[2];
  if (!SWIG_Python_UnpackTuple(args,(char*)"swiginit", 2, 2, obj)) {
    return NULL;
  } else {
    PySwigObject *sthis = SWIG_Python_GetSwigThis(obj[0]);
    if (sthis) {
      PySwigObject_append((PyObject*) sthis, obj[1]);
    } else {
      SWIG_Python_SetSwigThis(obj[0], obj[1]);
    }
    return SWIG_Py_Void();
  }
}

/* Create a new pointer object */

SWIGRUNTIME PyObject *
SWIG_Python_NewPointerObj(void *ptr, swig_type_info *type, int flags) {
  if (!ptr) {
    return SWIG_Py_Void();
  } else {
    int own = (flags & SWIG_POINTER_OWN) ? SWIG_POINTER_OWN : 0;
    PyObject *robj = PySwigObject_New(ptr, type, own);
    PySwigClientData *clientdata = type ? (PySwigClientData *)(type->clientdata) : 0;
    if (clientdata && !(flags & SWIG_POINTER_NOSHADOW)) {
      PyObject *inst = SWIG_Python_NewShadowInstance(clientdata, robj);
      if (inst) {
	Py_DECREF(robj);
	robj = inst;
      }
    }
    return robj;
  }
}

/* Create a new packed object */

SWIGRUNTIMEINLINE PyObject *
SWIG_Python_NewPackedObj(void *ptr, size_t sz, swig_type_info *type) {
  return ptr ? PySwigPacked_New((void *) ptr, sz, type) : SWIG_Py_Void();
}

/* -----------------------------------------------------------------------------*
 *  Get type list 
 * -----------------------------------------------------------------------------*/

#ifdef SWIG_LINK_RUNTIME
void *SWIG_ReturnGlobalTypeList(void *);
#endif

SWIGRUNTIME swig_module_info *
SWIG_Python_GetModule(void) {
  static void *type_pointer = (void *)0;
  /* first check if module already created */
  if (!type_pointer) {
#ifdef SWIG_LINK_RUNTIME
    type_pointer = SWIG_ReturnGlobalTypeList((void *)0);
#else
    type_pointer = PyCObject_Import((char*)"swig_runtime_data" SWIG_RUNTIME_VERSION,
				    (char*)"type_pointer" SWIG_TYPE_TABLE_NAME);
    if (PyErr_Occurred()) {
      PyErr_Clear();
      type_pointer = (void *)0;
    }
#endif
  }
  return (swig_module_info *) type_pointer;
}

#if PY_MAJOR_VERSION < 2
/* PyModule_AddObject function was introduced in Python 2.0.  The following function
   is copied out of Python/modsupport.c in python version 2.3.4 */
SWIGINTERN int
PyModule_AddObject(PyObject *m, char *name, PyObject *o)
{
  PyObject *dict;
  if (!PyModule_Check(m)) {
    PyErr_SetString(PyExc_TypeError,
		    "PyModule_AddObject() needs module as first arg");
    return SWIG_ERROR;
  }
  if (!o) {
    PyErr_SetString(PyExc_TypeError,
		    "PyModule_AddObject() needs non-NULL value");
    return SWIG_ERROR;
  }
  
  dict = PyModule_GetDict(m);
  if (dict == NULL) {
    /* Internal error -- modules must have a dict! */
    PyErr_Format(PyExc_SystemError, "module '%s' has no __dict__",
		 PyModule_GetName(m));
    return SWIG_ERROR;
  }
  if (PyDict_SetItemString(dict, name, o))
    return SWIG_ERROR;
  Py_DECREF(o);
  return SWIG_OK;
}
#endif

SWIGRUNTIME void
SWIG_Python_DestroyModule(void *vptr)
{
  swig_module_info *swig_module = (swig_module_info *) vptr;
  swig_type_info **types = swig_module->types;
  size_t i;
  for (i =0; i < swig_module->size; ++i) {
    swig_type_info *ty = types[i];
    if (ty->owndata) {
      PySwigClientData *data = (PySwigClientData *) ty->clientdata;
      if (data) PySwigClientData_Del(data);
    }
  }
  Py_DECREF(SWIG_This());
}

SWIGRUNTIME void
SWIG_Python_SetModule(swig_module_info *swig_module) {
  static PyMethodDef swig_empty_runtime_method_table[] = { {NULL, NULL, 0, NULL} };/* Sentinel */

  PyObject *module = Py_InitModule((char*)"swig_runtime_data" SWIG_RUNTIME_VERSION,
				   swig_empty_runtime_method_table);
  PyObject *pointer = PyCObject_FromVoidPtr((void *) swig_module, SWIG_Python_DestroyModule);
  if (pointer && module) {
    PyModule_AddObject(module, (char*)"type_pointer" SWIG_TYPE_TABLE_NAME, pointer);
  } else {
    Py_XDECREF(pointer);
  }
}

/* The python cached type query */
SWIGRUNTIME PyObject *
SWIG_Python_TypeCache(void) {
  static PyObject *SWIG_STATIC_POINTER(cache) = PyDict_New();
  return cache;
}

SWIGRUNTIME swig_type_info *
SWIG_Python_TypeQuery(const char *type)
{
  PyObject *cache = SWIG_Python_TypeCache();
  PyObject *key = PyString_FromString(type); 
  PyObject *obj = PyDict_GetItem(cache, key);
  swig_type_info *descriptor;
  if (obj) {
    descriptor = (swig_type_info *) PyCObject_AsVoidPtr(obj);
  } else {
    swig_module_info *swig_module = SWIG_Python_GetModule();
    descriptor = SWIG_TypeQueryModule(swig_module, swig_module, type);
    if (descriptor) {
      obj = PyCObject_FromVoidPtr(descriptor, NULL);
      PyDict_SetItem(cache, key, obj);
      Py_DECREF(obj);
    }
  }
  Py_DECREF(key);
  return descriptor;
}

/* 
   For backward compatibility only
*/
#define SWIG_POINTER_EXCEPTION  0
#define SWIG_arg_fail(arg)      SWIG_Python_ArgFail(arg)
#define SWIG_MustGetPtr(p, type, argnum, flags)  SWIG_Python_MustGetPtr(p, type, argnum, flags)

SWIGRUNTIME int
SWIG_Python_AddErrMesg(const char* mesg, int infront)
{
  if (PyErr_Occurred()) {
    PyObject *type = 0;
    PyObject *value = 0;
    PyObject *traceback = 0;
    PyErr_Fetch(&type, &value, &traceback);
    if (value) {
      PyObject *old_str = PyObject_Str(value);
      Py_XINCREF(type);
      PyErr_Clear();
      if (infront) {
	PyErr_Format(type, "%s %s", mesg, PyString_AsString(old_str));
      } else {
	PyErr_Format(type, "%s %s", PyString_AsString(old_str), mesg);
      }
      Py_DECREF(old_str);
    }
    return 1;
  } else {
    return 0;
  }
}
  
SWIGRUNTIME int
SWIG_Python_ArgFail(int argnum)
{
  if (PyErr_Occurred()) {
    /* add information about failing argument */
    char mesg[256];
    PyOS_snprintf(mesg, sizeof(mesg), "argument number %d:", argnum);
    return SWIG_Python_AddErrMesg(mesg, 1);
  } else {
    return 0;
  }
}

SWIGRUNTIMEINLINE const char *
PySwigObject_GetDesc(PyObject *self)
{
  PySwigObject *v = (PySwigObject *)self;
  swig_type_info *ty = v ? v->ty : 0;
  return ty ? ty->str : (char*)"";
}

SWIGRUNTIME void
SWIG_Python_TypeError(const char *type, PyObject *obj)
{
  if (type) {
#if defined(SWIG_COBJECT_TYPES)
    if (obj && PySwigObject_Check(obj)) {
      const char *otype = (const char *) PySwigObject_GetDesc(obj);
      if (otype) {
	PyErr_Format(PyExc_TypeError, "a '%s' is expected, 'PySwigObject(%s)' is received",
		     type, otype);
	return;
      }
    } else 
#endif      
    {
      const char *otype = (obj ? obj->ob_type->tp_name : 0); 
      if (otype) {
	PyObject *str = PyObject_Str(obj);
	const char *cstr = str ? PyString_AsString(str) : 0;
	if (cstr) {
	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s(%s)' is received",
		       type, otype, cstr);
	} else {
	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s' is received",
		       type, otype);
	}
	Py_XDECREF(str);
	return;
      }
    }   
    PyErr_Format(PyExc_TypeError, "a '%s' is expected", type);
  } else {
    PyErr_Format(PyExc_TypeError, "unexpected type is received");
  }
}


/* Convert a pointer value, signal an exception on a type mismatch */
SWIGRUNTIME void *
SWIG_Python_MustGetPtr(PyObject *obj, swig_type_info *ty, int argnum, int flags) {
  void *result;
  if (SWIG_Python_ConvertPtr(obj, &result, ty, flags) == -1) {
    PyErr_Clear();
    if (flags & SWIG_POINTER_EXCEPTION) {
      SWIG_Python_TypeError(SWIG_TypePrettyName(ty), obj);
      SWIG_Python_ArgFail(argnum);
    }
  }
  return result;
}


#ifdef __cplusplus
#if 0
{ /* cc-mode */
#endif
}
#endif
