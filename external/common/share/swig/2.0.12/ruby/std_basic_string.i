#if !defined(SWIG_STD_STRING) 
#define SWIG_STD_BASIC_STRING

%include <rubycontainer.swg>

#define %swig_basic_string(Type...)  %swig_sequence_methods_val(Type)


%traits_swigtype(std::basic_string<char>);
%fragment(SWIG_Traits_frag(std::basic_string<char>));


%fragment(SWIG_AsPtr_frag(std::basic_string<char>),"header",
	  fragment="SWIG_AsCharPtrAndSize") {
SWIGINTERN int
SWIG_AsPtr(std::basic_string<char>)(VALUE obj, std::string **val)
{
  static swig_type_info* string_info = 
    SWIG_TypeQuery("std::basic_string<char> *");
  std::string *vptr;    
  if (SWIG_ConvertPtr(obj, (void**)&vptr, string_info, 0) == SWIG_OK) {
    if (val) *val = vptr;
    return SWIG_OLDOBJ;
  } else {
    char* buf = 0 ; size_t size = 0; int alloc = 0;
    if (SWIG_AsCharPtrAndSize(obj, &buf, &size, &alloc) == SWIG_OK) {
      if (buf) {
	if (val) *val = new std::string(buf, size - 1);
	if (alloc == SWIG_NEWOBJ) %delete_array(buf);
	return SWIG_NEWOBJ;
      }
    }
    if (val) {
      rb_raise( rb_eTypeError, "a string is expected");
    }
    return 0;
  }
}  
}

%fragment(SWIG_From_frag(std::basic_string<char>),"header",
	  fragment="SWIG_FromCharPtrAndSize") {
SWIGINTERNINLINE VALUE
  SWIG_From(std::basic_string<char>)(const std::string& s)
  {
    return SWIG_FromCharPtrAndSize(s.data(), s.size());
  }
}

%include <std/std_basic_string.i>
%typemaps_asptrfromn(%checkcode(STRING), std::basic_string<char>);

#endif


#if !defined(SWIG_STD_WSTRING)

%fragment(SWIG_AsPtr_frag(std::basic_string<wchar_t>),"header",
	  fragment="SWIG_AsWCharPtrAndSize") {
SWIGINTERN int
  SWIG_AsPtr(std::basic_string<wchar_t>)(VALUE obj, std::wstring **val)
  {
    static swig_type_info* string_info = 
      SWIG_TypeQuery("std::basic_string<wchar_t> *");
    std::wstring *vptr;    
    if (SWIG_ConvertPtr(obj, (void**)&vptr, string_info, 0) == SWIG_OK) {
      if (val) *val = vptr;
      return SWIG_OLDOBJ;
    } else {
      wchar_t *buf = 0 ; size_t size = 0; int alloc = 0;
      if (SWIG_AsWCharPtrAndSize(obj, &buf, &size, &alloc) == SWIG_OK) {
	if (buf) {
	  if (val) *val = new std::wstring(buf, size - 1);
	  if (alloc == SWIG_NEWOBJ) %delete_array(buf);
	  return SWIG_NEWOBJ;
	}
      }
      if (val) {
	rb_raise( rb_eTypeError, "a string is expected");
      }
      return 0;
    }
  }
}

%fragment(SWIG_From_frag(std::basic_string<wchar_t>),"header",
	  fragment="SWIG_FromWCharPtrAndSize") {
SWIGINTERNINLINE VALUE
  SWIG_From(std::basic_string<wchar_t>)(const std::wstring& s)
  {
    return SWIG_FromWCharPtrAndSize(s.data(), s.size());
  }
}

%typemaps_asptrfromn(%checkcode(UNISTRING), std::basic_string<wchar_t>);

#endif
