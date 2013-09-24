/* ------------------------------------------------------------
 * Primitive Types
 * ------------------------------------------------------------ */

/* bool */

%fragment(SWIG_From_frag(bool),"header") {
SWIGINTERNINLINE SV *
SWIG_From_dec(bool)(bool value)
{    
  SV *obj = sv_newmortal();
  if (value) {
    sv_setsv(obj, &PL_sv_yes);
  } else {
    sv_setsv(obj, &PL_sv_no); 
  }
  return obj;
}
}

%fragment(SWIG_AsVal_frag(bool),"header",
	  fragment="SWIG_CanCastAsInteger") {
SWIGINTERN int
SWIG_AsVal_dec(bool)(SV *obj, bool* val)
{
  if (obj == &PL_sv_yes) {
    if (val) *val = true;
    return SWIG_OK;
  } else if (obj == &PL_sv_no) { 
    if (val) *val = false;
    return SWIG_OK;
  } else {
    if (val) *val = SvTRUE(obj) ? true: false;
    return SWIG_AddCast(SWIG_OK);    
  }
  return SWIG_TypeError;
}
}


/* long */

%fragment(SWIG_From_frag(long),"header") {
SWIGINTERNINLINE SV *
SWIG_From_dec(long)(long value)
{    
  SV *obj = sv_newmortal();
  sv_setiv(obj, (IV) value);
  return obj;
}
}

%fragment(SWIG_AsVal_frag(long),"header",
	  fragment="SWIG_CanCastAsInteger") {
SWIGINTERN int
SWIG_AsVal_dec(long)(SV *obj, long* val)
{
  if (SvIOK(obj)) {
    if (val) *val = SvIV(obj);
    return SWIG_OK;
  } else {
    int dispatch = 0;
    const char *nptr = SvPV_nolen(obj);
    if (nptr) {
      char *endptr;
      long v;
      errno = 0;
      v = strtol(nptr, &endptr,0);
      if (errno == ERANGE) {
	errno = 0;
	return SWIG_OverflowError;
      } else {
	if (*endptr == '\0') {
	  if (val) *val = v;
	  return SWIG_Str2NumCast(SWIG_OK);
	}
      }
    }
    if (!dispatch) {
      double d;
      int res = SWIG_AddCast(SWIG_AsVal(double)(obj,&d));
      if (SWIG_IsOK(res) && SWIG_CanCastAsInteger(&d, LONG_MIN, LONG_MAX)) {
	if (val) *val = (long)(d);
	return res;
      }
    }
  }
  return SWIG_TypeError;
}
}

/* unsigned long */

%fragment(SWIG_From_frag(unsigned long),"header",
	  fragment=SWIG_AsVal_frag(double)) {
SWIGINTERNINLINE SV *
SWIG_From_dec(unsigned long)(unsigned long value)
{    
  SV *obj = sv_newmortal();
  sv_setuv(obj, (UV) value);
  return obj;
}
}

%fragment(SWIG_AsVal_frag(unsigned long),"header",
	  fragment="SWIG_CanCastAsInteger") {
SWIGINTERN int
SWIG_AsVal_dec(unsigned long)(SV *obj, unsigned long *val) 
{
  if (SvUOK(obj)) {
    if (val) *val = SvUV(obj);
    return SWIG_OK;
  } else  if (SvIOK(obj)) {
    long v = SvIV(obj);
    if (v >= 0) {
      if (val) *val = v;
      return SWIG_OK;
    } else {
      return SWIG_OverflowError;
    }
  } else {
    int dispatch = 0;
    const char *nptr = SvPV_nolen(obj);
    if (nptr) {
      char *endptr;
      unsigned long v;
      errno = 0;
      v = strtoul(nptr, &endptr,0);
      if (errno == ERANGE) {
	errno = 0;
	return SWIG_OverflowError;
      } else {
	if (*endptr == '\0') {
	  if (val) *val = v;
	  return SWIG_Str2NumCast(SWIG_OK);
	}
      }
    }
    if (!dispatch) {
      double d;
      int res = SWIG_AddCast(SWIG_AsVal(double)(obj,&d));
      if (SWIG_IsOK(res) && SWIG_CanCastAsInteger(&d, 0, ULONG_MAX)) {
	if (val) *val = (unsigned long)(d);
	return res;
      }
    }
  }
  return SWIG_TypeError;
}
}

/* long long */

%fragment(SWIG_From_frag(long long),"header",
	  fragment=SWIG_From_frag(long),
	  fragment="<limits.h>",
	  fragment="<stdio.h>") {
SWIGINTERNINLINE SV *
SWIG_From_dec(long long)(long long value)
{
  if (((long long) LONG_MIN <= value) && (value <= (long long) LONG_MAX)) {
    return SWIG_From(long)(%numeric_cast(value,long));
  } else {    
    char temp[256]; 
    SV *obj = sv_newmortal();
    sprintf(temp, "%lld", value);
    sv_setpv(obj, temp);
    return obj;
  }
}
}

%fragment(SWIG_AsVal_frag(long long),"header",
	  fragment="<limits.h>",
	  fragment="<stdlib.h>",
	  fragment="SWIG_CanCastAsInteger") {

SWIGINTERN int
SWIG_AsVal_dec(long long)(SV *obj, long long *val)
{
  if (SvIOK(obj)) {
    if (val) *val = SvIV(obj);
    return SWIG_OK;
  } else {
    int dispatch = 0;
    const char *nptr = SvPV_nolen(obj);
    if (nptr) {
      char *endptr;
      long long v;
      errno = 0;
      v = strtoll(nptr, &endptr,0);
      if (errno == ERANGE) {
	errno = 0;
	return SWIG_OverflowError;
      } else {
	if (*endptr == '\0') {
	  if (val) *val = v;
	  return SWIG_Str2NumCast(SWIG_OK);
	}
      }
    }
    if (!dispatch) {
      const double mant_max = 1LL << DBL_MANT_DIG;
      const double mant_min = -mant_max;
      double d;
      int res = SWIG_AddCast(SWIG_AsVal(double)(obj,&d));
      if (SWIG_IsOK(res) && SWIG_CanCastAsInteger(&d, mant_min, mant_max)) {
	if (val) *val = (long long)(d);
	return res;
      }
    }
  }
  return SWIG_TypeError; 
}
}

/* unsigned long long */

%fragment(SWIG_From_frag(unsigned long long),"header",
	  fragment=SWIG_From_frag(long long),
	  fragment="<limits.h>",
	  fragment="<stdio.h>") {
SWIGINTERNINLINE SV *
SWIG_From_dec(unsigned long long)(unsigned long long value)
{
  if (value < (unsigned long long) LONG_MAX) {
    return SWIG_From(long long)(%numeric_cast(value, long long));
  } else {
    char temp[256]; 
    SV *obj = sv_newmortal();
    sprintf(temp, "%llu", value);
    sv_setpv(obj, temp);
    return obj;
  }
}
}

%fragment(SWIG_AsVal_frag(unsigned long long),"header",
	  fragment="<limits.h>",
	  fragment="<stdlib.h>",
	  fragment="SWIG_CanCastAsInteger") {
SWIGINTERN int
SWIG_AsVal_dec(unsigned long long)(SV *obj, unsigned long long *val)
{ 
  if (SvUOK(obj)) {
    if (val) *val = SvUV(obj);
    return SWIG_OK;
  } else  if (SvIOK(obj)) {
    long v = SvIV(obj);
    if (v >= 0) {
      if (val) *val = v;
      return SWIG_OK;
    } else {
      return SWIG_OverflowError;
    }
  } else {
    int dispatch = 0;
    const char *nptr = SvPV_nolen(obj);
    if (nptr) {
      char *endptr;
      unsigned long long v;
      errno = 0;
      v = strtoull(nptr, &endptr,0);
      if (errno == ERANGE) {
	errno = 0;
	return SWIG_OverflowError;
      } else {
	if (*endptr == '\0') {
	  if (val) *val = v;
	  return SWIG_Str2NumCast(SWIG_OK);
	}
      }
    }
    if (!dispatch) {
      const double mant_max = 1LL << DBL_MANT_DIG;
      double d;
      int res = SWIG_AddCast(SWIG_AsVal(double)(obj,&d));
      if (SWIG_IsOK(res) && SWIG_CanCastAsInteger(&d, 0, mant_max)) {
	if (val) *val = (unsigned long long)(d);
	return res;
      }
    }
  }
  return SWIG_TypeError;
}
}

/* double */

%fragment(SWIG_From_frag(double),"header") {
SWIGINTERNINLINE SV *
SWIG_From_dec(double)(double value)
{    
  SV *obj = sv_newmortal();
  sv_setnv(obj, value);
  return obj;
}
}

%fragment(SWIG_AsVal_frag(double),"header") {
SWIGINTERN int
SWIG_AsVal_dec(double)(SV *obj, double *val)
{
  if (SvNIOK(obj)) {
    if (val) *val = SvNV(obj);
    return SWIG_OK;
  } else if (SvIOK(obj)) {
    if (val) *val = (double) SvIV(obj);
    return SWIG_AddCast(SWIG_OK);
  } else {
    const char *nptr = SvPV_nolen(obj);
    if (nptr) {
      char *endptr;
      double v = strtod(nptr, &endptr);
      if (errno == ERANGE) {
	errno = 0;
	return SWIG_OverflowError;
      } else {
	if (*endptr == '\0') {
	  if (val) *val = v;
	  return SWIG_Str2NumCast(SWIG_OK);
	}
      }
    }
  }
  return SWIG_TypeError;
}
}
