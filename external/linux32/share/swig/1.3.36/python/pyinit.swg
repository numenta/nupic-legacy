/* ------------------------------------------------------------
 * The start of the Python initialization function 
 * ------------------------------------------------------------ */

%insert(init) "swiginit.swg"

%init %{

#ifdef __cplusplus
extern "C" {
#endif

/* Python-specific SWIG API */
#define SWIG_newvarlink()                             SWIG_Python_newvarlink()
#define SWIG_addvarlink(p, name, get_attr, set_attr)  SWIG_Python_addvarlink(p, name, get_attr, set_attr)
#define SWIG_InstallConstants(d, constants)           SWIG_Python_InstallConstants(d, constants)
 
/* -----------------------------------------------------------------------------
 * global variable support code.
 * ----------------------------------------------------------------------------- */
 
typedef struct swig_globalvar {   
  char       *name;                  /* Name of global variable */
  PyObject *(*get_attr)(void);       /* Return the current value */
  int       (*set_attr)(PyObject *); /* Set the value */
  struct swig_globalvar *next;
} swig_globalvar;

typedef struct swig_varlinkobject {
  PyObject_HEAD
  swig_globalvar *vars;
} swig_varlinkobject;

SWIGINTERN PyObject *
swig_varlink_repr(swig_varlinkobject *SWIGUNUSEDPARM(v)) {
  return PyString_FromString("<Swig global variables>");
}

SWIGINTERN PyObject *
swig_varlink_str(swig_varlinkobject *v) {
  PyObject *str = PyString_FromString("(");
  swig_globalvar  *var;
  for (var = v->vars; var; var=var->next) {
    PyString_ConcatAndDel(&str,PyString_FromString(var->name));
    if (var->next) PyString_ConcatAndDel(&str,PyString_FromString(", "));
  }
  PyString_ConcatAndDel(&str,PyString_FromString(")"));
  return str;
}

SWIGINTERN int
swig_varlink_print(swig_varlinkobject *v, FILE *fp, int SWIGUNUSEDPARM(flags)) {
  PyObject *str = swig_varlink_str(v);
  fprintf(fp,"Swig global variables ");
  fprintf(fp,"%s\n", PyString_AsString(str));
  Py_DECREF(str);
  return 0;
}

SWIGINTERN void
swig_varlink_dealloc(swig_varlinkobject *v) {
  swig_globalvar *var = v->vars;
  while (var) {
    swig_globalvar *n = var->next;
    free(var->name);
    free(var);
    var = n;
  }
}

SWIGINTERN PyObject *
swig_varlink_getattr(swig_varlinkobject *v, char *n) {
  PyObject *res = NULL;
  swig_globalvar *var = v->vars;
  while (var) {
    if (strcmp(var->name,n) == 0) {
      res = (*var->get_attr)();
      break;
    }
    var = var->next;
  }
  if (res == NULL && !PyErr_Occurred()) {
    PyErr_SetString(PyExc_NameError,"Unknown C global variable");
  }
  return res;
}

SWIGINTERN int
swig_varlink_setattr(swig_varlinkobject *v, char *n, PyObject *p) {
  int res = 1;
  swig_globalvar *var = v->vars;
  while (var) {
    if (strcmp(var->name,n) == 0) {
      res = (*var->set_attr)(p);
      break;
    }
    var = var->next;
  }
  if (res == 1 && !PyErr_Occurred()) {
    PyErr_SetString(PyExc_NameError,"Unknown C global variable");
  }
  return res;
}

SWIGINTERN PyTypeObject*
swig_varlink_type(void) {
  static char varlink__doc__[] = "Swig var link object";
  static PyTypeObject varlink_type;
  static int type_init = 0;  
  if (!type_init) {
    const PyTypeObject tmp
      = {
      PyObject_HEAD_INIT(NULL)
      0,                                  /* Number of items in variable part (ob_size) */
      (char *)"swigvarlink",              /* Type name (tp_name) */
      sizeof(swig_varlinkobject),         /* Basic size (tp_basicsize) */
      0,                                  /* Itemsize (tp_itemsize) */
      (destructor) swig_varlink_dealloc,   /* Deallocator (tp_dealloc) */ 
      (printfunc) swig_varlink_print,     /* Print (tp_print) */
      (getattrfunc) swig_varlink_getattr, /* get attr (tp_getattr) */
      (setattrfunc) swig_varlink_setattr, /* Set attr (tp_setattr) */
      0,                                  /* tp_compare */
      (reprfunc) swig_varlink_repr,       /* tp_repr */
      0,                                  /* tp_as_number */
      0,                                  /* tp_as_sequence */
      0,                                  /* tp_as_mapping */
      0,                                  /* tp_hash */
      0,                                  /* tp_call */
      (reprfunc)swig_varlink_str,        /* tp_str */
      0,                                  /* tp_getattro */
      0,                                  /* tp_setattro */
      0,                                  /* tp_as_buffer */
      0,                                  /* tp_flags */
      varlink__doc__,                     /* tp_doc */
      0,                                  /* tp_traverse */
      0,                                  /* tp_clear */
      0,                                  /* tp_richcompare */
      0,                                  /* tp_weaklistoffset */
#if PY_VERSION_HEX >= 0x02020000
      0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_iter -> tp_weaklist */
#endif
#if PY_VERSION_HEX >= 0x02030000
      0,                                  /* tp_del */
#endif
#ifdef COUNT_ALLOCS
      0,0,0,0                             /* tp_alloc -> tp_next */
#endif
    };
    varlink_type = tmp;
    varlink_type.ob_type = &PyType_Type;
    type_init = 1;
  }
  return &varlink_type;
}

/* Create a variable linking object for use later */
SWIGINTERN PyObject *
SWIG_Python_newvarlink(void) {
  swig_varlinkobject *result = PyObject_NEW(swig_varlinkobject, swig_varlink_type());
  if (result) {
    result->vars = 0;
  }
  return ((PyObject*) result);
}

SWIGINTERN void 
SWIG_Python_addvarlink(PyObject *p, char *name, PyObject *(*get_attr)(void), int (*set_attr)(PyObject *p)) {
  swig_varlinkobject *v = (swig_varlinkobject *) p;
  swig_globalvar *gv = (swig_globalvar *) malloc(sizeof(swig_globalvar));
  if (gv) {
    size_t size = strlen(name)+1;
    gv->name = (char *)malloc(size);
    if (gv->name) {
      strncpy(gv->name,name,size);
      gv->get_attr = get_attr;
      gv->set_attr = set_attr;
      gv->next = v->vars;
    }
  }
  v->vars = gv;
}

SWIGINTERN PyObject *
SWIG_globals(void) {
  static PyObject *_SWIG_globals = 0; 
  if (!_SWIG_globals) _SWIG_globals = SWIG_newvarlink();  
  return _SWIG_globals;
}

/* -----------------------------------------------------------------------------
 * constants/methods manipulation
 * ----------------------------------------------------------------------------- */

/* Install Constants */
SWIGINTERN void
SWIG_Python_InstallConstants(PyObject *d, swig_const_info constants[]) {
  PyObject *obj = 0;
  size_t i;
  for (i = 0; constants[i].type; ++i) {
    switch(constants[i].type) {
    case SWIG_PY_POINTER:
      obj = SWIG_NewPointerObj(constants[i].pvalue, *(constants[i]).ptype,0);
      break;
    case SWIG_PY_BINARY:
      obj = SWIG_NewPackedObj(constants[i].pvalue, constants[i].lvalue, *(constants[i].ptype));
      break;
    default:
      obj = 0;
      break;
    }
    if (obj) {
      PyDict_SetItemString(d, constants[i].name, obj);
      Py_DECREF(obj);
    }
  }
}

/* -----------------------------------------------------------------------------*/
/* Fix SwigMethods to carry the callback ptrs when needed */
/* -----------------------------------------------------------------------------*/

SWIGINTERN void
SWIG_Python_FixMethods(PyMethodDef *methods,
		       swig_const_info *const_table,
		       swig_type_info **types,
		       swig_type_info **types_initial) {
  size_t i;
  for (i = 0; methods[i].ml_name; ++i) {
    const char *c = methods[i].ml_doc;
    if (c && (c = strstr(c, "swig_ptr: "))) {
      int j;
      swig_const_info *ci = 0;
      const char *name = c + 10;
      for (j = 0; const_table[j].type; ++j) {
	if (strncmp(const_table[j].name, name, 
		    strlen(const_table[j].name)) == 0) {
	  ci = &(const_table[j]);
	  break;
	}
      }
      if (ci) {
	size_t shift = (ci->ptype) - types;
	swig_type_info *ty = types_initial[shift];
	size_t ldoc = (c - methods[i].ml_doc);
	size_t lptr = strlen(ty->name)+2*sizeof(void*)+2;
	char *ndoc = (char*)malloc(ldoc + lptr + 10);
	if (ndoc) {
	  char *buff = ndoc;
	  void *ptr = (ci->type == SWIG_PY_POINTER) ? ci->pvalue : 0;
	  if (ptr) {
	    strncpy(buff, methods[i].ml_doc, ldoc);
	    buff += ldoc;
	    strncpy(buff, "swig_ptr: ", 10);
	    buff += 10;
	    SWIG_PackVoidPtr(buff, ptr, ty->name, lptr);
	    methods[i].ml_doc = ndoc;
	  }
	}
      }
    }
  }
} 

#ifdef __cplusplus
}
#endif

/* -----------------------------------------------------------------------------*
 *  Partial Init method
 * -----------------------------------------------------------------------------*/

#ifdef __cplusplus
extern "C"
#endif
SWIGEXPORT void SWIG_init(void) {
  PyObject *m, *d;
  
  /* Fix SwigMethods to carry the callback ptrs when needed */
  SWIG_Python_FixMethods(SwigMethods, swig_const_table, swig_types, swig_type_initial);
  
  m = Py_InitModule((char *) SWIG_name, SwigMethods);
  d = PyModule_GetDict(m);
  
  SWIG_InitializeModule(0);
  SWIG_InstallConstants(d,swig_const_table);
  
%}

