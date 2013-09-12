/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * wchar.i
 *
 * Typemaps for the wchar_t type
 * These are mapped to a C# String and are passed around by value.
 *
 * Support code for wide strings can be turned off by defining SWIG_CSHARP_NO_WSTRING_HELPER
 *
 * ----------------------------------------------------------------------------- */

#if !defined(SWIG_CSHARP_NO_WSTRING_HELPER)
#if !defined(SWIG_CSHARP_WSTRING_HELPER_)
#define SWIG_CSHARP_WSTRING_HELPER_
%insert(runtime) %{
/* Callback for returning strings to C# without leaking memory */
typedef void * (SWIGSTDCALL* SWIG_CSharpWStringHelperCallback)(const wchar_t *);
static SWIG_CSharpWStringHelperCallback SWIG_csharp_wstring_callback = NULL;
%}

%pragma(csharp) imclasscode=%{
  protected class SWIGWStringHelper {

    public delegate string SWIGWStringDelegate(IntPtr message);
    static SWIGWStringDelegate wstringDelegate = new SWIGWStringDelegate(CreateWString);

    [DllImport("$dllimport", EntryPoint="SWIGRegisterWStringCallback_$module")]
    public static extern void SWIGRegisterWStringCallback_$module(SWIGWStringDelegate wstringDelegate);

    static string CreateWString([MarshalAs(UnmanagedType.LPWStr)]IntPtr cString) {
      return System.Runtime.InteropServices.Marshal.PtrToStringUni(cString);
    }

    static SWIGWStringHelper() {
      SWIGRegisterWStringCallback_$module(wstringDelegate);
    }
  }

  static protected SWIGWStringHelper swigWStringHelper = new SWIGWStringHelper();
%}

%insert(runtime) %{
#ifdef __cplusplus
extern "C"
#endif
SWIGEXPORT void SWIGSTDCALL SWIGRegisterWStringCallback_$module(SWIG_CSharpWStringHelperCallback callback) {
  SWIG_csharp_wstring_callback = callback;
}
%}
#endif // SWIG_CSHARP_WSTRING_HELPER_
#endif // SWIG_CSHARP_NO_WSTRING_HELPER


// wchar_t
%typemap(ctype) wchar_t "wchar_t"
%typemap(imtype) wchar_t "char"
%typemap(cstype) wchar_t "char"

%typemap(csin) wchar_t "$csinput"
%typemap(csout, excode=SWIGEXCODE) wchar_t {
    char ret = $imcall;$excode
    return ret;
  }
%typemap(csvarin, excode=SWIGEXCODE2) wchar_t %{
    set {
      $imcall;$excode
    } %}
%typemap(csvarout, excode=SWIGEXCODE2) wchar_t %{
    get {
      char ret = $imcall;$excode
      return ret;
    } %}

%typemap(in) wchar_t %{ $1 = ($1_ltype)$input; %}
%typemap(out) wchar_t %{ $result = (wchar_t)$1; %}

%typemap(typecheck) wchar_t = char;

// wchar_t *
%typemap(ctype) wchar_t * "wchar_t *"
%typemap(imtype, inattributes="[MarshalAs(UnmanagedType.LPWStr)]", out="IntPtr" ) wchar_t * "string"
%typemap(cstype) wchar_t * "string"

%typemap(csin) wchar_t * "$csinput"
%typemap(csout, excode=SWIGEXCODE) wchar_t * {
    string ret = System.Runtime.InteropServices.Marshal.PtrToStringUni($imcall);$excode
    return ret;
  }
%typemap(csvarin, excode=SWIGEXCODE2) wchar_t * %{
    set {
      $imcall;$excode
    } %}
%typemap(csvarout, excode=SWIGEXCODE2) wchar_t * %{
    get {
      string ret = $imcall;$excode
      return ret;
    } %}

%typemap(in) wchar_t * %{ $1 = ($1_ltype)$input; %}
%typemap(out) wchar_t * %{ $result = (wchar_t *)$1; %}

%typemap(typecheck) wchar_t * = char *;

