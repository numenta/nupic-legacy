%ensure_fragment(SWIG_AsWCharPtrAndSize)
%ensure_fragment(SWIG_FromWCharPtrAndSize)


%types(wchar_t *);

%fragment("SWIG_pwchar_descriptor","header") {
SWIGINTERN swig_type_info*
SWIG_pwchar_descriptor()
{
  static int init = 0;
  static swig_type_info* info = 0;
  if (!init) {
    info = SWIG_TypeQuery("_p_wchar_t");
    init = 1;
  }
  return info;
}
}

%include <typemaps/strings.swg>
%typemaps_string(%checkcode(UNISTRING), %checkcode(UNICHAR),
		 wchar_t, WChar, SWIG_AsWCharPtrAndSize, SWIG_FromWCharPtrAndSize, wcslen,
		"<wchar.h>", WCHAR_MIN, WCHAR_MAX)

