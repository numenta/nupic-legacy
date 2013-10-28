%include <typemaps/valtypes.swg>

%fragment(SWIG_AsVal_frag(jstring),"header") {
SWIGINTERN int
SWIG_AsVal_dec(jstring)(Tcl_Obj * obj, jstring *val)
{
  int len = 0;
  const char *cstr = Tcl_GetStringFromObj(obj, &len);
  if (!cstr || (strcmp(cstr,"NULL") == 0)) {
    if (val) *val = 0;
    return SWIG_OK;
  } else {
    int len = 0;
    const Tcl_UniChar *ucstr = Tcl_GetUnicodeFromObj(obj,&len);
    if (val) {
      *val = JvNewString((const jchar*)ucstr, len);
    }
  }
  
  return SWIG_NEWOBJ;
}
}

%fragment(SWIG_From_frag(jstring),"header") {
SWIGINTERNINLINE Tcl_Obj *
SWIG_From_dec(jstring)(jstring val)
{
  if (!val) {
    return Tcl_NewStringObj("NULL",-1);
  } else {
    return Tcl_NewUnicodeObj((Tcl_UniChar *)JvGetStringChars(val),JvGetStringUTFLength(val));
  }
}
}

%typemaps_asvalfrom(%checkcode(STRING),
		    %arg(SWIG_AsVal(jstring)), 
		    %arg(SWIG_From(jstring)), 
		    %arg(SWIG_AsVal_frag(jstring)), 
		    %arg(SWIG_From_frag(jstring)), 
		    java::lang::String *);

