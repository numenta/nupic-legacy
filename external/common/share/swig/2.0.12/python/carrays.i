%define %array_class(TYPE,NAME)
#if defined(SWIGPYTHON_BUILTIN)
  %feature("python:slot", "sq_item", functype="ssizeargfunc") NAME::__getitem__;
  %feature("python:slot", "sq_ass_item", functype="ssizeobjargproc") NAME::__setitem__;

%inline %{
typedef struct {
    TYPE *el;
} NAME;
%}

%extend NAME {

  NAME(size_t nelements) {
      NAME *arr = %new_instance(NAME);
      arr->el = %new_array(nelements, TYPE);
      return arr;
  }

  ~NAME() {
      %delete_array(self->el);
      %delete(self);
  }
  
  TYPE __getitem__(size_t index) {
      return self->el[index];
  }

  void __setitem__(size_t index, TYPE value) {
      self->el[index] = value;
  }

  TYPE * cast() {
      return self->el;
  }

  static NAME *frompointer(TYPE *t) {
      return %reinterpret_cast(t, NAME *);
  }
};

%types(NAME = TYPE);

#else
  %array_class_wrap(TYPE,NAME,__getitem__,__setitem__)
#endif
%enddef

%include <typemaps/carrays.swg>




