%include <typemaps/valtypes.swg>

%fragment(SWIG_AsVal_frag(jstring),"header") {
SWIGINTERN int
SWIG_AsVal(jstring)(VALUE obj, jstring *val)
{
  if (NIL_P(obj)){
    if (val) *val = 0;
    return SWIG_OK;
  } 
  if (TYPE(obj) == T_STRING) {
    if (val) {
      char *cstr = rb_string_value_ptr(&(obj));
      jsize len = RSTRING_LEN(obj);
      *val = JvNewStringLatin1(cstr, len);
    }
    return SWIG_NEWOBJ;
  }
  return SWIG_TypeError;
}
}

%fragment(SWIG_From_frag(jstring),"header") {
SWIGINTERNINLINE VALUE
SWIG_From(jstring)(jstring val)
{
  if (!val) {
    return Qnil;
  } else {
    jint len = JvGetStringUTFLength(val);
    char buf[len];
    JvGetStringUTFRegion(val, 0, len, buf);
    return rb_str_new(buf,len);
  }
}
}

%typemaps_asvalfrom(%checkcode(STRING),
		    %arg(SWIG_AsVal(jstring)), 
		    %arg(SWIG_From(jstring)), 
		    %arg(SWIG_AsVal_frag(jstring)), 
		    %arg(SWIG_From_frag(jstring)), 
		    java::lang::String *);

