
%define CONVERT_BOOL_IN(lvar,t,invar)
  convert_to_boolean_ex(invar);
  lvar = (t) Z_LVAL_PP(invar);
%enddef

%define CONVERT_INT_IN(lvar,t,invar)
  convert_to_long_ex(invar);
  lvar = (t) Z_LVAL_PP(invar);
%enddef

%define CONVERT_LONG_LONG_IN(lvar,t,invar)
  switch ((*(invar))->type) {
      case IS_DOUBLE:
          lvar = (t) (*(invar))->value.dval;
          break;
      case IS_STRING: {
          char * endptr;
          errno = 0;
          lvar = (t) strtoll((*(invar))->value.str.val, &endptr, 10);
          if (*endptr && !errno) break;
          /* FALL THRU */
      }
      default:
          convert_to_long_ex(invar);
          lvar = (t) (*(invar))->value.lval;
  }
%enddef

%define CONVERT_UNSIGNED_LONG_LONG_IN(lvar,t,invar)
  switch ((*(invar))->type) {
      case IS_DOUBLE:
          lvar = (t) (*(invar))->value.dval;
          break;
      case IS_STRING: {
          char * endptr;
          errno = 0;
          lvar = (t) strtoull((*(invar))->value.str.val, &endptr, 10);
          if (*endptr && !errno) break;
          /* FALL THRU */
      }
      default:
          convert_to_long_ex(invar);
          lvar = (t) (*(invar))->value.lval;
  }
%enddef

%define CONVERT_INT_OUT(lvar,invar)
  lvar = (t) Z_LVAL_PP(invar);
%enddef

%define CONVERT_FLOAT_IN(lvar,t,invar)
  convert_to_double_ex(invar);
  lvar = (t) Z_DVAL_PP(invar);
%enddef

%define CONVERT_CHAR_IN(lvar,t,invar)
  convert_to_string_ex(invar);
  lvar = (t) *Z_STRVAL_PP(invar);
%enddef

%define CONVERT_STRING_IN(lvar,t,invar)
  if ((*invar)->type==IS_NULL) {
    lvar = (t) 0;
  } else {
    convert_to_string_ex(invar);
    lvar = (t) Z_STRVAL_PP(invar);
  }
%enddef

%define %pass_by_val( TYPE, CONVERT_IN )
%typemap(in) TYPE
%{
  CONVERT_IN($1,$1_ltype,$input);
%}
%typemap(in) const TYPE & ($*1_ltype temp)
%{
  CONVERT_IN(temp,$*1_ltype,$input);
  $1 = &temp;
%}
%typemap(directorout) TYPE
%{
  CONVERT_IN($result,$1_ltype,$input);
%}
%typemap(directorout) const TYPE & ($*1_ltype temp)
%{
  CONVERT_IN(temp,$*1_ltype,$input);
  $result = &temp;
%}
%enddef

%fragment("t_output_helper","header") %{
static void
t_output_helper( zval **target, zval *o) {
  if ( (*target)->type == IS_ARRAY ) {
    /* it's already an array, just append */
    add_next_index_zval( *target, o );
    return;
  }
  if ( (*target)->type == IS_NULL ) {
    REPLACE_ZVAL_VALUE(target,o,1);
    FREE_ZVAL(o);
    return;
  }
  zval *tmp;
  ALLOC_INIT_ZVAL(tmp);
  *tmp = **target;
  zval_copy_ctor(tmp);
  array_init(*target);
  add_next_index_zval( *target, tmp);
  add_next_index_zval( *target, o);

}
%}
