/* -----------------------------------------------------------------------------
 * js_ctor:  template for wrapping a ctor.
 *   - $jswrapper:        wrapper of called ctor
 *   - $jslocals:         locals part of wrapper
 *   - $jscode:           code part of wrapper
 *   - $jsargcount:       number of arguments
 *   - $jsmangledtype:    mangled type of class
 * ----------------------------------------------------------------------------- */

%fragment("js_ctor", "templates") %{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args) {
  v8::HandleScope scope;
  v8::Handle<v8::Object> self = args.Holder();
  $jslocals
  if(args.Length() != $jsargcount) SWIG_exception_fail(SWIG_ERROR, "Illegal number of arguments for $jswrapper.");
  $jscode

  SWIGV8_SetPrivateData(self, result, SWIGTYPE_$jsmangledtype, SWIG_POINTER_OWN);
  SWIGV8_RETURN(self);

  goto fail;
fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_veto_ctor:  a vetoing ctor for abstract classes
 *   - $jswrapper:        name of wrapper
 *   - $jsname:           class name
 * ----------------------------------------------------------------------------- */
%fragment ("js_veto_ctor", "templates")
%{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args) {
  v8::HandleScope scope;
  SWIG_exception(SWIG_ERROR, "Class $jsname can not be instantiated");
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_ctor_dispatcher:  dispatcher for overloaded constructors
 *   - $jswrapper:        name of wrapper
 *   - $jsname:           class name
 *   - $jsdispatchcases:  part containing code for dispatching
 * ----------------------------------------------------------------------------- */
%fragment ("js_ctor_dispatcher", "templates")
%{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args) {
  v8::HandleScope scope;
  OverloadErrorHandler errorHandler;
  v8::Handle<v8::Value> self;

  // switch all cases by means of series of if-returns.
  $jsdispatchcases

  // default:
  SWIG_exception_fail(SWIG_ERROR, "Illegal arguments for construction of $jsmangledname");

fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_overloaded_ctor:  template for wrapping a ctor.
 *   - $jswrapper:        wrapper of called ctor
 *   - $jslocals:         locals part of wrapper
 *   - $jscode:           code part of wrapper
 *   - $jsargcount:       number of arguments
 *   - $jsmangledtype:    mangled type of class
 * ----------------------------------------------------------------------------- */
%fragment("js_overloaded_ctor", "templates") %{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args, V8ErrorHandler& SWIGV8_ErrorHandler) {
  v8::HandleScope scope;
  v8::Handle<v8::Object> self = args.Holder();
  $jslocals
  if(args.Length() != $jsargcount) SWIG_exception_fail(SWIG_ERROR, "Illegal number of arguments for $jswrapper.");
  $jscode

  SWIGV8_SetPrivateData(self, result, SWIGTYPE_$jsmangledtype, SWIG_POINTER_OWN);
  SWIGV8_RETURN(self);

  goto fail;
fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_ctor_dispatch_case:  template for a dispatch case for calling an overloaded ctor.
 *   - $jsargcount:       number of arguments of called ctor
 *   - $jswrapper:        wrapper of called ctor
 *
 *  Note: a try-catch-like mechanism is used to switch cases
 * ----------------------------------------------------------------------------- */
%fragment ("js_ctor_dispatch_case", "templates")
%{
  if(args.Length() == $jsargcount) {
    errorHandler.err.Clear();
#if SWIG_V8_VERSION < 0x031900
    self = $jswrapper(args, errorHandler);
    if(errorHandler.err.IsEmpty()) {
      return scope.Close(self);
    }
#else
    $jswrapper(args, errorHandler);
    if(errorHandler.err.IsEmpty()) {
      return;
    }
#endif
  }
%}

/* -----------------------------------------------------------------------------
 * js_dtor:  template for a destructor wrapper
 *   - $jsmangledname:  mangled class name
 *   - $jstype:         class type
 * ----------------------------------------------------------------------------- */
%fragment ("js_dtor", "templates")
%{

#if (SWIG_V8_VERSION < 0x031900)
void $jswrapper(v8::Persistent< v8::Value > object, void *parameter)
{
  SWIGV8_Proxy *proxy = static_cast<SWIGV8_Proxy *>(parameter);
#else
void $jswrapper(v8::Isolate *isolate, v8::Persistent< v8::Object > * object, SWIGV8_Proxy *proxy)
{
#endif

  if(proxy->swigCMemOwn && proxy->swigCObject) {
#ifdef SWIGRUNTIME_DEBUG
    printf("Deleting wrapped instance: %s\n", proxy->info->name);
#endif
    $jsfree proxy->swigCObject;
  }
  delete proxy;

  object.Clear();
#if (SWIG_V8_VERSION < 0x031900)
  object.Dispose();
#elif (SWIG_V8_VERSION < 0x032100)
  object->Dispose(isolate);
#else
  object->Dispose();
#endif
}
%}

/* -----------------------------------------------------------------------------
 * js_dtoroverride:  template for a destructor wrapper
 *   - $jsmangledname:  mangled class name
 *   - $jstype:         class type
 *   - ${destructor_action}: The custom destructor action to invoke.
 * ----------------------------------------------------------------------------- */
%fragment ("js_dtoroverride", "templates")
%{
#if (SWIG_V8_VERSION < 0x031900)
void $jswrapper(v8::Persistent< v8::Value > object, void *parameter)
{
  SWIGV8_Proxy *proxy = static_cast<SWIGV8_Proxy *>(parameter);
#else
void $jswrapper(v8::Isolate *isolate, v8::Persistent< v8::Object > * object, SWIGV8_Proxy *proxy)
{
#endif
  if(proxy->swigCMemOwn && proxy->swigCObject) {
    $jstype arg1 = ($jstype)proxy->swigCObject;
    ${destructor_action}
  }
  delete proxy;

#if (SWIG_V8_VERSION < 0x031900)
  object.Dispose();
#elif (SWIG_V8_VERSION < 0x032100)
  object->Dispose(isolate);
#else
  object->Dispose();
#endif
}
%}

/* -----------------------------------------------------------------------------
 * js_getter:  template for getter function wrappers
 *   - $jswrapper:  wrapper function name
 *   - $jslocals:   locals part of wrapper
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment("js_getter", "templates")
%{
SwigV8ReturnValue $jswrapper(v8::Local<v8::String> property, const SwigV8PropertyCallbackInfo& info) {
  v8::HandleScope scope;
  v8::Handle<v8::Value> jsresult;
  $jslocals
  $jscode
  SWIGV8_RETURN_INFO(jsresult, info);

  goto fail;
fail:
  SWIGV8_RETURN_INFO(v8::Undefined(), info);
}
%}

/* -----------------------------------------------------------------------------
 * js_setter:  template for setter function wrappers
 *   - $jswrapper:  wrapper function name
 *   - $jslocals:   locals part of wrapper
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment("js_setter", "templates")
%{
void $jswrapper(v8::Local<v8::String> property, v8::Local<v8::Value> value,
  const SwigV8PropertyCallbackInfoVoid& info) {
  v8::HandleScope scope;
  $jslocals
  $jscode
  goto fail;
fail:
  return;
}
%}

/* -----------------------------------------------------------------------------
 * js_function:  template for function wrappers
 *   - $jswrapper:  wrapper function name
 *   - $jslocals:   locals part of wrapper
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment("js_function", "templates")
%{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args) {
  v8::HandleScope scope;
  v8::Handle<v8::Value> jsresult;
  $jslocals
  if(args.Length() != $jsargcount) SWIG_exception_fail(SWIG_ERROR, "Illegal number of arguments for $jswrapper.");

  $jscode
  SWIGV8_RETURN(jsresult);

  goto fail;
fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_function_dispatcher:  template for a function dispatcher for overloaded functions
 *   - $jswrapper:  wrapper function name
 *   - $jsname:     name of the wrapped function
 *   - $jslocals:   locals part of wrapper
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment("js_function_dispatcher", "templates")
%{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args) {
  v8::HandleScope scope;
  v8::Handle<v8::Value> jsresult;
  OverloadErrorHandler errorHandler;
  $jscode

  SWIG_exception_fail(SWIG_ERROR, "Illegal arguments for function $jsname.");

  goto fail;
fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_overloaded_function:  template for a overloaded function
 *   - $jswrapper:  wrapper function name
 *   - $jslocals:   locals part of wrapper
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment ("js_overloaded_function", "templates")
%{
SwigV8ReturnValue $jswrapper(const SwigV8Arguments& args, V8ErrorHandler& SWIGV8_ErrorHandler)
{
  v8::HandleScope scope;
  v8::Handle<v8::Value> jsresult;
  $jslocals
  $jscode
  SWIGV8_RETURN(jsresult);

  goto fail;
fail:
  SWIGV8_RETURN(v8::Undefined());
}
%}

/* -----------------------------------------------------------------------------
 * js_function_dispatch_case:  template for a case used in the function dispatcher
 *   - $jswrapper:  wrapper function name
 *   - $jsargcount: number of arguments of overloaded function
 *   - $jscode:     code part of wrapper
 * ----------------------------------------------------------------------------- */
%fragment ("js_function_dispatch_case", "templates")
%{

  if(args.Length() == $jsargcount) {
    errorHandler.err.Clear();
#if (SWIG_V8_VERSION < 0x031900)
    jsresult = $jswrapper(args, errorHandler);
    if(errorHandler.err.IsEmpty()) {
      return scope.Close(jsresult);
    }
#else
    $jswrapper(args, errorHandler);
    if(errorHandler.err.IsEmpty()) {
      return;
    }
#endif
  }
%}

/* -----------------------------------------------------------------------------
 * jsv8_declare_class_template:  template for a class template declaration.
 *   - $jsmangledname:  mangled class name
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_declare_class_template", "templates")
%{
  SWIGV8_ClientData $jsmangledname_clientData;
%}

/* -----------------------------------------------------------------------------
 * jsv8_define_class_template:  template for a class template definition.
 *   - $jsmangledname:  mangled class name
 *   - $jsmangledtype:  mangled class type
 *   - $jsdtor:         the dtor wrapper
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_define_class_template", "templates")
%{
  v8::Handle<v8::FunctionTemplate> $jsmangledname_class = SWIGV8_CreateClassTemplate("$jsmangledname");
#if (SWIG_V8_VERSION < 0x031900)
  $jsmangledname_clientData.class_templ = v8::Persistent<v8::FunctionTemplate>::New($jsmangledname_class);
#else
  $jsmangledname_clientData.class_templ.Reset(v8::Isolate::GetCurrent(), $jsmangledname_class);
#endif
  $jsmangledname_clientData.dtor = $jsdtor;
  if (SWIGTYPE_$jsmangledtype->clientdata == 0) {
    SWIGTYPE_$jsmangledtype->clientdata = &$jsmangledname_clientData;
  }
%}


/* -----------------------------------------------------------------------------
 * jsv8_inherit:  template for an class inherit statement.
 *   - $jsmangledname:  mangled class name
 *   - $jsbaseclass:    mangled name of the base class
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_inherit", "templates")
%{
  if (SWIGTYPE_p$jsbaseclass->clientdata && !(static_cast<SWIGV8_ClientData *>(SWIGTYPE_p$jsbaseclass->clientdata)->class_templ.IsEmpty()))
  {
#if (SWIG_V8_VERSION < 0x031900)
    $jsmangledname_class->Inherit(static_cast<SWIGV8_ClientData *>(SWIGTYPE_p$jsbaseclass->clientdata)->class_templ);
#else
    $jsmangledname_class->Inherit(
      v8::Handle<v8::FunctionTemplate>::New(
        v8::Isolate::GetCurrent(),
        static_cast<SWIGV8_ClientData *>(SWIGTYPE_p$jsbaseclass->clientdata)->class_templ)
     );
#endif

#ifdef SWIGRUNTIME_DEBUG
    printf("Inheritance successful $jsmangledname $jsbaseclass\n");
#endif
  } else {
#ifdef SWIGRUNTIME_DEBUG
    printf("Unable to inherit baseclass, it didn't exist $jsmangledname $jsbaseclass\n");
#endif
  }
%}

/* -----------------------------------------------------------------------------
 * jsv8_create_class_instance:  template for creating an class object.
 *   - $jsname:         class name
 *   - $jsmangledname:  mangled class name
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_create_class_instance", "templates")
%{
  v8::Handle<v8::FunctionTemplate> $jsmangledname_class_0 = SWIGV8_CreateClassTemplate("$jsname");
  $jsmangledname_class_0->SetCallHandler($jsctor);
  $jsmangledname_class_0->Inherit($jsmangledname_class);
  $jsmangledname_class_0->SetHiddenPrototype(true);
  v8::Handle<v8::Object> $jsmangledname_obj = $jsmangledname_class_0->GetFunction();
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_class:  template for a statement that registers a class in a parent namespace.
 *   - $jsname:         class name
 *   - $jsmangledname:  mangled class name
 *   - $jsparent:       mangled name of parent namespace
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_class", "templates")
%{
  $jsparent_obj->Set(v8::String::NewSymbol("$jsname"), $jsmangledname_obj);
%}

/* -----------------------------------------------------------------------------
 * jsv8_create_namespace:  template for a statement that creates a namespace object.
 *   - $jsmangledname:  mangled namespace name
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_create_namespace", "templates")
%{
  v8::Handle<v8::Object> $jsmangledname_obj = v8::Object::New();
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_namespace:  template for a statement that registers a namespace in a parent namespace.
 *   - $jsname:         name of namespace
 *   - $jsmangledname:  mangled name of namespace
 *   - $jsparent:       mangled name of parent namespace
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_namespace", "templates")
%{
  $jsparent_obj->Set(v8::String::NewSymbol("$jsname"), $jsmangledname_obj);
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_member_function:  template for a statement that registers a member function.
 *   - $jsmangledname:  mangled class name
 *   - $jsname:         name of the function
 *   - $jswrapper:      wrapper of the member function
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_member_function", "templates")
%{
  SWIGV8_AddMemberFunction($jsmangledname_class, "$jsname", $jswrapper);
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_member_variable:  template for a statement that registers a member variable.
 *   - $jsmangledname:  mangled class name
 *   - $jsname:         name of the function
 *   - $jsgetter:       wrapper of the getter function
 *   - $jssetter:       wrapper of the setter function
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_member_variable", "templates")
%{
  SWIGV8_AddMemberVariable($jsmangledname_class, "$jsname", $jsgetter, $jssetter);
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_static_function:  template for a statement that registers a static class function.
 *   - $jsname:         function name
 *   - $jswrapper:      wrapper of the function
 *   - $jsparent:       mangled name of parent namespace
 *
 * Note: this template is also used for global functions.
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_static_function", "templates")
%{
  SWIGV8_AddStaticFunction($jsparent_obj, "$jsname", $jswrapper);
%}

/* -----------------------------------------------------------------------------
 * jsv8_register_static_variable:  template for a statement that registers a static variable.
 *   - $jsname:         variable name
 *   - $jsparent:       mangled name of parent namespace
 *   - $jsgetter:       wrapper of the getter function
 *   - $jssetter:       wrapper of the setter function
 *
 * Note: this template is also used for global variables.
 * ----------------------------------------------------------------------------- */
%fragment("jsv8_register_static_variable", "templates")
%{
  SWIGV8_AddStaticVariable($jsparent_obj, "$jsname", $jsgetter, $jssetter);
%}
