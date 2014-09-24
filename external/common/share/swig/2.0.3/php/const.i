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
  /* This actually registers it as a global variable and constant.  I don't
   * like it, but I can't figure out the zend_constant code... */
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  SWIG_SetPointerZval(z_var, (void*)$value, $1_descriptor, 0);
  /* zend_hash_add(&EG(symbol_table), "$1", sizeof("$1"), (void *)&z_var,sizeof(zval *), NULL); */
  zend_constant c;
  c.value = *z_var;
  zval_copy_ctor(&c.value);
  size_t len = sizeof("$1") - 1;
  c.name = zend_strndup("$1", len);
  c.name_len = len+1;
  c.flags = CONST_CS | CONST_PERSISTENT;
  c.module_number = module_number;
  zend_register_constant( &c TSRMLS_CC );
}

/* Handled as a global variable. */
%typemap(consttab) SWIGTYPE (CLASS::*) "";
