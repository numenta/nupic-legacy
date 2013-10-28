/* -----------------------------------------------------------------------------
 * const.i
 *
 * Typemaps for constants
 * ----------------------------------------------------------------------------- */

%typemap(consttab) int,
                   unsigned int,
                   short,
                   unsigned short,
                   long,
                   unsigned long,
                   unsigned char,
                   signed char,
                   bool,
                   enum SWIGTYPE
  "SWIG_LONG_CONSTANT($symname, $value);";

%typemap(consttab) float,
                   double
  "SWIG_DOUBLE_CONSTANT($symname, $value);";

%typemap(consttab) char
  "SWIG_CHAR_CONSTANT($symname, $value);";

%typemap(consttab) char *,
                   const char *,
                   char [],
                   const char []
  "SWIG_STRING_CONSTANT($symname, $value);";

%typemap(consttab) SWIGTYPE *,
                   SWIGTYPE &,
                   SWIGTYPE [] {
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  SWIG_SetPointerZval(z_var, (void*)$value, $1_descriptor, 0);
  zend_constant c;
  c.value = *z_var;
  zval_copy_ctor(&c.value);
  size_t len = sizeof("$symname") - 1;
  c.name = zend_strndup("$symname", len);
  c.name_len = len+1;
  c.flags = CONST_CS | CONST_PERSISTENT;
  c.module_number = module_number;
  zend_register_constant( &c TSRMLS_CC );
}

/* Handled as a global variable. */
%typemap(consttab) SWIGTYPE (CLASS::*) "";
