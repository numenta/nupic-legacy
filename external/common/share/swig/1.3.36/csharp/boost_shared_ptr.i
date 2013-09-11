%include <shared_ptr.i>

%define SWIG_SHARED_PTR_TYPEMAPS(PROXYCLASS, CONST, TYPE...)

%naturalvar TYPE;
%naturalvar SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >;

// destructor mods
%feature("unref") TYPE 
//"if (debug_shared) { cout << \"deleting use_count: \" << (*smartarg1).use_count() << \" [\" << (boost::get_deleter<SWIG_null_deleter>(*smartarg1) ? std::string(\"CANNOT BE DETERMINED SAFELY\") : ( (*smartarg1).get() ? (*smartarg1)->getValue() : std::string(\"NULL PTR\") )) << \"]\" << endl << flush; }\n"
                               "(void)arg1; delete smartarg1;"


// plain value
%typemap(in, canthrow=1) CONST TYPE ($&1_type argp = 0) %{
  argp = ((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input) ? ((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input)->get() : 0;
  if (!argp) {
    SWIG_CSharpSetPendingExceptionArgument(SWIG_CSharpArgumentNullException, "Attempt to dereference null $1_type", 0);
    return $null;
  }
  $1 = *argp; %}
%typemap(out) CONST TYPE 
%{ $result = new SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >(new $1_ltype(($1_ltype &)$1)); %}

// plain pointer
%typemap(in, canthrow=1) CONST TYPE * (SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *smartarg = 0) %{
  smartarg = (SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input;
  $1 = (TYPE *)(smartarg ? smartarg->get() : 0); %}
%typemap(out, fragment="SWIG_null_deleter") CONST TYPE * %{
  $result = $1 ? new SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >($1 SWIG_NO_NULL_DELETER_$owner) : 0;
%}

// plain reference
%typemap(in, canthrow=1) CONST TYPE & %{
  $1 = ($1_ltype)(((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input) ? ((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input)->get() : 0);
  if(!$1) {
    SWIG_CSharpSetPendingExceptionArgument(SWIG_CSharpArgumentNullException, "$1_type reference is null", 0);
    return $null;
  } %}
%typemap(out, fragment="SWIG_null_deleter") CONST TYPE &
%{ $result = new SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >($1 SWIG_NO_NULL_DELETER_$owner); %}

// plain pointer by reference
%typemap(in) CONST TYPE *& ($*1_ltype temp = 0)
%{ temp = (((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input) ? ((SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *)$input)->get() : 0);
   $1 = &temp; %}
%typemap(out, fragment="SWIG_null_deleter") CONST TYPE *&
%{ $result = new SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >(*$1 SWIG_NO_NULL_DELETER_$owner); %}

// shared_ptr by value
%typemap(in) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >
%{ if ($input) $1 = *($&1_ltype)$input; %}
%typemap(out) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >
%{ $result = $1 ? new $1_ltype($1) : 0; %}

// shared_ptr by reference
%typemap(in, canthrow=1) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > & ($*1_ltype tempnull)
%{ $1 = $input ? ($1_ltype)$input : &tempnull; %}
%typemap(out) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > &
%{ $result = *$1 ? new $*1_ltype(*$1) : 0; %} 

// shared_ptr by pointer
%typemap(in) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > * ($*1_ltype tempnull)
%{ $1 = $input ? ($1_ltype)$input : &tempnull; %}
%typemap(out, fragment="SWIG_null_deleter") SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *
%{ $result = ($1 && *$1) ? new $*1_ltype(*($1_ltype)$1) : 0;
   if ($owner) delete $1; %}

// shared_ptr by pointer reference
%typemap(in) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& (SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > tempnull, $*1_ltype temp = 0)
%{ temp = $input ? *($1_ltype)&$input : &tempnull;
   $1 = &temp; %}
%typemap(out) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *&
%{ *($1_ltype)&$result = (*$1 && **$1) ? new SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >(**$1) : 0; %} 

// various missing typemaps - If ever used (unlikely) ensure compilation error rather than runtime bug
%typemap(in) CONST TYPE[], CONST TYPE[ANY], CONST TYPE (CLASS::*) %{
#error "typemaps for $1_type not available"
%}
%typemap(out) CONST TYPE[], CONST TYPE[ANY], CONST TYPE (CLASS::*) %{
#error "typemaps for $1_type not available"
%}


%typemap (ctype)  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >, 
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > &,
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *,
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& "void *"
%typemap (imtype, out="IntPtr") SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >, 
                                SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > &,
                                SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *,
                                SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& "HandleRef"
%typemap (cstype) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >, 
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > &,
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *,
                  SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& "PROXYCLASS"

%typemap(csin) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >, 
               SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > &,
               SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *,
               SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& "PROXYCLASS.getCPtr($csinput)"

%typemap(csout, excode=SWIGEXCODE) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > & {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > * {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > *& {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }


%typemap(csout, excode=SWIGEXCODE) CONST TYPE {
    PROXYCLASS ret = new PROXYCLASS($imcall, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) CONST TYPE & {
    PROXYCLASS ret = new PROXYCLASS($imcall, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) CONST TYPE * {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }
%typemap(csout, excode=SWIGEXCODE) CONST TYPE *& {
    IntPtr cPtr = $imcall;
    PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
    return ret;
  }

%typemap(csvarout, excode=SWIGEXCODE2) CONST TYPE & %{
    get {
      $csclassname ret = new $csclassname($imcall, true);$excode
      return ret;
    } %}
%typemap(csvarout, excode=SWIGEXCODE2) CONST TYPE * %{
    get {
      IntPtr cPtr = $imcall;
      $csclassname ret = (cPtr == IntPtr.Zero) ? null : new $csclassname(cPtr, true);$excode
      return ret;
    } %}

%typemap(csvarout, excode=SWIGEXCODE2) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > & %{
    get {
      IntPtr cPtr = $imcall;
      PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
      return ret;
    } %}
%typemap(csvarout, excode=SWIGEXCODE2) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > * %{
    get {
      IntPtr cPtr = $imcall;
      PROXYCLASS ret = (cPtr == IntPtr.Zero) ? null : new PROXYCLASS(cPtr, true);$excode
      return ret;
    } %}


// Proxy classes (base classes, ie, not derived classes)
%typemap(csbody) TYPE %{
  private HandleRef swigCPtr;
  private bool swigCMemOwnBase;

  internal $csclassname(IntPtr cPtr, bool cMemoryOwn) {
    swigCMemOwnBase = cMemoryOwn;
    swigCPtr = new HandleRef(this, cPtr);
  }

  internal static HandleRef getCPtr($csclassname obj) {
    return (obj == null) ? new HandleRef(null, IntPtr.Zero) : obj.swigCPtr;
  }
%}

// Derived proxy classes
%typemap(csbody_derived) TYPE %{
  private HandleRef swigCPtr;
  private bool swigCMemOwnDerived;

  internal $csclassname(IntPtr cPtr, bool cMemoryOwn) : base($imclassname.$csclassname_SWIGSharedPtrUpcast(cPtr), true) {
    swigCMemOwnDerived = cMemoryOwn;
    swigCPtr = new HandleRef(this, cPtr);
  }

  internal static HandleRef getCPtr($csclassname obj) {
    return (obj == null) ? new HandleRef(null, IntPtr.Zero) : obj.swigCPtr;
  }
%}

%typemap(csdestruct, methodname="Dispose", methodmodifiers="public") TYPE {
    lock(this) {
      if(swigCPtr.Handle != IntPtr.Zero && swigCMemOwnBase) {
        swigCMemOwnBase = false;
        $imcall;
      }
      swigCPtr = new HandleRef(null, IntPtr.Zero);
      GC.SuppressFinalize(this);
    }
  }

%typemap(csdestruct_derived, methodname="Dispose", methodmodifiers="public") TYPE {
    lock(this) {
      if(swigCPtr.Handle != IntPtr.Zero && swigCMemOwnDerived) {
        swigCMemOwnDerived = false;
        $imcall;
      }
      swigCPtr = new HandleRef(null, IntPtr.Zero);
      GC.SuppressFinalize(this);
      base.Dispose();
    }
  }

%typemap(imtype) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > swigSharedPtrUpcast "IntPtr"
%typemap(csin) SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE > swigSharedPtrUpcast "PROXYCLASS.getCPtr($csinput).Handle"


%template() SWIG_SHARED_PTR_QNAMESPACE::shared_ptr< CONST TYPE >;
%enddef

