%insert(runtime) %{

// Note: since 3.19 there are new CallBack types, since 03.21.9 the old ones have been removed
#if SWIG_V8_VERSION < 0x031900
typedef v8::InvocationCallback  SwigV8FunctionCallback;
typedef v8::AccessorGetter      SwigV8AccessorGetterCallback;
typedef v8::AccessorSetter      SwigV8AccessorSetterCallback;
typedef v8::AccessorInfo        SwigV8PropertyCallbackInfoVoid;
#else
typedef v8::FunctionCallback            SwigV8FunctionCallback;
typedef v8::AccessorGetterCallback      SwigV8AccessorGetterCallback;
typedef v8::AccessorSetterCallback      SwigV8AccessorSetterCallback;
typedef v8::PropertyCallbackInfo<void>  SwigV8PropertyCallbackInfoVoid;
#endif

/**
 * Creates a class template for a class with specified initialization function.
 */
SWIGRUNTIME v8::Handle<v8::FunctionTemplate> SWIGV8_CreateClassTemplate(const char* symbol) {
    v8::HandleScope scope;
    v8::Local<v8::FunctionTemplate> class_templ = v8::FunctionTemplate::New();
    class_templ->SetClassName(v8::String::NewSymbol(symbol));

    v8::Handle<v8::ObjectTemplate> inst_templ = class_templ->InstanceTemplate();
    inst_templ->SetInternalFieldCount(1);

    v8::Handle<v8::ObjectTemplate> equals_templ = class_templ->PrototypeTemplate();
    equals_templ->Set(v8::String::NewSymbol("equals"), v8::FunctionTemplate::New(_SWIGV8_wrap_equals));

    v8::Handle<v8::ObjectTemplate> cptr_templ = class_templ->PrototypeTemplate();
    cptr_templ->Set(v8::String::NewSymbol("getCPtr"), v8::FunctionTemplate::New(_wrap_getCPtr));

    return scope.Close(class_templ);
}

/**
 * Registers a class method with given name for a given class template.
 */
SWIGRUNTIME void SWIGV8_AddMemberFunction(v8::Handle<v8::FunctionTemplate> class_templ, const char* symbol,
  SwigV8FunctionCallback _func) {
    v8::Handle<v8::ObjectTemplate> proto_templ = class_templ->PrototypeTemplate();
    proto_templ->Set(v8::String::NewSymbol(symbol), v8::FunctionTemplate::New(_func));
}

/**
 * Registers a class property with given name for a given class template.
 */
SWIGRUNTIME void SWIGV8_AddMemberVariable(v8::Handle<v8::FunctionTemplate> class_templ, const char* symbol,
  SwigV8AccessorGetterCallback getter, SwigV8AccessorSetterCallback setter) {
  v8::Handle<v8::ObjectTemplate> proto_templ = class_templ->InstanceTemplate();
  proto_templ->SetAccessor(v8::String::NewSymbol(symbol), getter, setter);
}

/**
 * Registers a class method with given name for a given object.
 */
SWIGRUNTIME void SWIGV8_AddStaticFunction(v8::Handle<v8::Object> obj, const char* symbol,
  const SwigV8FunctionCallback& _func) {
  obj->Set(v8::String::NewSymbol(symbol), v8::FunctionTemplate::New(_func)->GetFunction());
}

/**
 * Registers a class method with given name for a given object.
 */
SWIGRUNTIME void SWIGV8_AddStaticVariable(v8::Handle<v8::Object> obj, const char* symbol,
  SwigV8AccessorGetterCallback getter, SwigV8AccessorSetterCallback setter) {
  obj->SetAccessor(v8::String::NewSymbol(symbol), getter, setter);
}

SWIGRUNTIME void JS_veto_set_variable(v8::Local<v8::String> property, v8::Local<v8::Value> value,
  const SwigV8PropertyCallbackInfoVoid& info)
{
    char buffer[256];
    char msg[512];
    int res;

    property->WriteUtf8(buffer, 256);
    res = sprintf(msg, "Tried to write read-only variable: %s.", buffer);

    if(res<0) {
      SWIG_exception(SWIG_ERROR, "Tried to write read-only variable.");
    } else {
      SWIG_exception(SWIG_ERROR, msg);
    }
}

%} // v8_helper_functions
