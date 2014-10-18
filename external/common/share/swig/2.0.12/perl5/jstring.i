%include <typemaps/valtypes.swg>

%fragment(SWIG_AsVal_frag(jstring),"header") {
SWIGINTERN int
SWIG_AsVal_dec(jstring)(SV *obj, jstring *val)
{
  if (SvPOK(obj)) {
    if (val) {
      STRLEN len = 0;
      char *cstr = SvPV(obj, len); 
      *val = JvNewStringLatin1(cstr, len);
    }
    return SWIG_OK;
  }
  return SWIG_ERROR;
}
}

%fragment(SWIG_From_frag(jstring),"header") {
SWIGINTERNINLINE SV *
SWIG_From_dec(jstring)(jstring val)
{
  SV *obj = sv_newmortal();
  if (!val) {
    sv_setsv(obj, &PL_sv_undef);
  } else {
    jsize len = JvGetStringUTFLength(val);
    if (!len) {
      sv_setsv(obj, &PL_sv_undef);
    } else {
      char *tmp = %new_array(len, char);
      JvGetStringUTFRegion(val, 0, len, tmp);
      sv_setpvn(obj, tmp, len);
      SvUTF8_on(obj);
      %delete_array(tmp);
    }
  }
  return obj;
}
}

%typemaps_asvalfrom(%checkcode(STRING),
		    %arg(SWIG_AsVal(jstring)), 
		    %arg(SWIG_From(jstring)), 
		    %arg(SWIG_AsVal_frag(jstring)), 
		    %arg(SWIG_From_frag(jstring)), 
		    java::lang::String *);

