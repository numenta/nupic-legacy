/* -----------------------------------------------------------------------------
 * Python API portion that goes into the runtime
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus
extern "C" {
#if 0
} /* cc-mode */
#endif
#endif

/* -----------------------------------------------------------------------------
 * Constant declarations
 * ----------------------------------------------------------------------------- */

/* Constant Types */
#define SWIG_PY_POINTER 4
#define SWIG_PY_BINARY  5

/* Constant information structure */
typedef struct swig_const_info {
  int type;
  char *name;
  long lvalue;
  double dvalue;
  void   *pvalue;
  swig_type_info **ptype;
} swig_const_info;

#ifdef __cplusplus
#if 0
{ /* cc-mode */
#endif
}
#endif

