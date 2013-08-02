/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * globalvar.i
 *
 * Global variables - add the variable to PHP
 * ----------------------------------------------------------------------------- */

%typemap(varinit) char *,
                  char []
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  z_var->type = IS_STRING;
  if($1) {
      z_var->value.str.val = estrdup($1);
      z_var->value.str.len = strlen($1);
  } else {
      z_var->value.str.val = 0;
      z_var->value.str.len = 0;
  }
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var, sizeof(zval *), NULL);
}

%typemap(varinit) int,
	          unsigned int,
                  unsigned short,
                  short,
                  unsigned short,
                  long,
                  unsigned long,
                  signed char,
                  unsigned char,
                  enum SWIGTYPE
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  z_var->type = IS_LONG;
  z_var->value.lval = $1;
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var, sizeof(zval *), NULL);
}

%typemap(varinit) bool
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  z_var->type = IS_BOOL;
  z_var->value.lval = ($1)?1:0;
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var, sizeof(zval *), NULL);
}

%typemap(varinit) float, double
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  z_var->type = IS_DOUBLE;
  z_var->value.dval = $1;
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var,
  sizeof(zval *), NULL);
}

%typemap(varinit) char
{
  zval *z_var;
  char c[2];
  MAKE_STD_ZVAL(z_var);
  c[0] = $1;
  c[1] = 0;
  z_var->type = IS_STRING;
  z_var->value.str.val = estrndup(c, 1);
  z_var->value.str.len = 1;
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var,
  sizeof(zval *), NULL);
}

%typemap(varinit) SWIGTYPE *, SWIGTYPE []
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  SWIG_SetPointerZval(z_var, (void*)$1, $1_descriptor, 0);
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void *)&z_var,
  sizeof(zval *), NULL);
}

%typemap(varinit) SWIGTYPE, SWIGTYPE &
{
  zval *z_var;

  MAKE_STD_ZVAL(z_var);
  SWIG_SetPointerZval(z_var, (void*)&$1, $&1_descriptor, 0);
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void*)&z_var,
  sizeof(zval *), NULL);
}

%typemap(varinit) char [ANY]
{
  zval *z_var;
  MAKE_STD_ZVAL(z_var);
  z_var->type = IS_STRING;
  if ($1) {
    // varinit char [ANY]
    ZVAL_STRINGL(z_var,(char*)$1, $1_dim0, 1);
  }
  zend_hash_add(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void*)&z_var, sizeof(zval *), NULL);
}

%typemap(varin) int, unsigned int, short, unsigned short, long, unsigned long, signed char, unsigned char,  enum SWIGTYPE
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  convert_to_long_ex(z_var);
  if ($1 != ($1_ltype)((*z_var)->value.lval)) {
    $1 = Z_LVAL_PP(z_var);
  }
}

%typemap(varin) bool
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  convert_to_boolean_ex(z_var);
  if ($1 != ($1_ltype)((*z_var)->value.lval)) {
    $1 = Z_LVAL_PP(z_var);
  }
}

%typemap(varin) double,float
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  convert_to_double_ex(z_var);
  if ($1 != ($1_ltype)((*z_var)->value.dval)) {
    $1 = Z_DVAL_PP(z_var);
  }
}

%typemap(varin) char
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  convert_to_string_ex(z_var);
  if ($1 != *((*z_var)->value.str.val)) {
    $1 = *((*z_var)->value.str.val);
  }
}

%typemap(varin) char *
{
  zval **z_var;
  char *s1;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  convert_to_string_ex(z_var);
  s1 = Z_STRVAL_PP(z_var);
  if ((s1 == NULL) || ($1 == NULL) || zend_binary_strcmp(s1, strlen(s1), $1, strlen($1))) {
    if (s1)
      $1 = estrdup(s1);
    else
      $1 = NULL;
  }
}


%typemap(varin) SWIGTYPE []
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1) {
    SWIG_SetPointerZval(*z_var, (void*)$1, $1_descriptor, $owner);
  }
}

%typemap(varin) char [ANY]
{
 zval **z_var;
 char *s1;

 zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
 s1 = Z_STRVAL_PP(z_var);
 if((s1 == NULL) || ($1 == NULL) || zend_binary_strcmp(s1, strlen(s1), $1, strlen($1))) {
  if(s1)
    strncpy($1, s1, $1_dim0);
 }
}

%typemap(varin) SWIGTYPE
{
  zval **z_var;
  $&1_ltype _temp;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if (SWIG_ConvertPtr(*z_var, (void**)&_temp, $&1_descriptor, 0) < 0) {
    SWIG_PHP_Error(E_ERROR,"Type error in value of $symname. Expected $&1_descriptor");
  }

  $1 = *($&1_ltype)_temp;

}

%typemap(varin) SWIGTYPE *, SWIGTYPE &
{
  zval **z_var;
  $1_ltype _temp;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if (SWIG_ConvertPtr(*z_var, (void **)&_temp, $1_descriptor, 0) < 0) { 
    SWIG_PHP_Error(E_ERROR,"Type error in value of $symname. Expected $&1_descriptor");
  }

  $1 = ($1_ltype)_temp;
}

%typemap(varout) int,
                 unsigned int,
                 unsigned short,
                 short,
                 long,
                 unsigned long,
                 signed char,
                 unsigned char,
                 enum SWIGTYPE
{
  zval **z_var;
  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1 != ($1_ltype)((*z_var)->value.lval)) {
    (*z_var)->value.lval = (long)$1;
  }
}

//SAMFIX need to cast zval->type, what if zend-hash_find fails? etc?
%typemap(varout) bool
{
  zval **z_var;
  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1 != ($1_ltype)((*z_var)->value.lval)) {
    (*z_var)->value.lval = (long)$1;
  }
}

%typemap(varout) double, float
{
  zval **z_var;
  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1 != ($1_ltype)((*z_var)->value.dval)) {
    (*z_var)->value.dval = (double)$1;
  }
}

%typemap(varout) char
{
  zval **z_var;
  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1 != *((*z_var)->value.str.val)) {
    char c[2];
    efree((*z_var)->value.str.val);
    c[0] = $1;
    c[1] = 0;
    (*z_var)->value.str.val = estrdup(c);
  }
}

%typemap(varout) char *
{
  zval **z_var;
  char *s1;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  s1 = Z_STRVAL_PP(z_var);
  if((s1 == NULL) || ($1 == NULL) || zend_binary_strcmp(s1, strlen(s1), $1, strlen($1) )) {
    if(s1)
      efree(s1);
    if($1) {
      (*z_var)->value.str.val = estrdup($1);
      (*z_var)->value.str.len = strlen($1) +1;
    } else {
      (*z_var)->value.str.val = 0;
      (*z_var)->value.str.len = 0;
    }
 }
}

%typemap(varout) SWIGTYPE
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  SWIG_SetPointerZval(*z_var, (void*)&$1, $&1_descriptor, 0);
}

%typemap(varout) SWIGTYPE []
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  if($1) 
  	SWIG_SetPointerZval(*z_var, (void*)$1, $1_descriptor, 0);
}

%typemap(varout) char [ANY]
{
  zval **z_var;
  char *s1;
deliberate error cos this code looks bogus to me
  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  s1 = Z_STRVAL_PP(z_var);
  if((s1 == NULL) || zend_binary_strcmp(s1, strlen(s1), $1, strlen($1))) {
    if($1) {
      (*z_var)->value.str.val = estrdup($1);
      (*z_var)->value.str.len = strlen($1)+1;
    } else {
      (*z_var)->value.str.val = 0;
      (*z_var)->value.str.len = 0;
    }
  }
}

%typemap(varout) SWIGTYPE *, SWIGTYPE &
{
  zval **z_var;

  zend_hash_find(&EG(symbol_table), (char*)"$1", sizeof("$1"), (void**)&z_var);
  SWIG_SetPointerZval(*z_var, (void*)$1, $1_descriptor, 0);
}


