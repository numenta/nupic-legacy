#ifdef __cplusplus

/*
  GC_VALUE is used as a replacement of Ruby's VALUE.
  GC_VALUE automatically handles registering and unregistering
  of the underlying Ruby object with the GC.

  It can be used if you want to create STL containers of VALUEs, such as:
  
     std::vector< GC_VALUE >;

  or as a member variable:
  
     struct A {
       GC_VALUE _obj;
       A(VALUE o) : _obj(o) {
       }
     };

   or as a input/output value (not much use for this, as VALUE works just as
   well here, thou):

     GC_VALUE func(GC_VALUE obj) { 
       GC_VALUE out = rb_obj_classname(obj);
       return out;
     }


   GC_VALUE is 'visible' at the wrapped side, so you can do:

      %template(RubyVector) std::vector<swig::GC_VALUE>;

   and all the proper typemaps will be used.
   
*/

namespace swig {

  %nodirector GC_VALUE;

  // We ignore the constructor so that user can never create a GC_VALUE 
  // manually
  %ignore GC_VALUE::GC_VALUE;

  struct GC_VALUE {
    VALUE inspect() const;
    VALUE to_s() const;
    GC_VALUE();
  protected:
    GC_VALUE( const GC_VALUE& );
    ~GC_VALUE();
  };

  %exception GC_VALUE {};


  %apply VALUE   {GC_VALUE};

  // Make sure this is the last typecheck done
  %typecheck(999999,noblock=1) GC_VALUE, GC_VALUE&, 
    const GC_VALUE& { $1 = 1; };

  /* For input */
  %typemap(in,noblock=1) GC_VALUE* (GC_VALUE r), GC_VALUE& (GC_VALUE r)  {
     r = $input; $1 = &r;
   }

  /* For output */
  %typemap(out,noblock=1)  GC_VALUE {
    $result = (VALUE)$1;
  }
  
  %typemap(out,noblock=1)  GC_VALUE*, GC_VALUE const & {
    $result = (VALUE)*$1;
  }

  %ignore LANGUAGE_OBJ;
  typedef GC_VALUE LANGUAGE_OBJ;
}


%{
namespace swig {
  class GC_VALUE {
  protected:
    // Hash of all GC_VALUE's currently in use
    static VALUE _hash;

    VALUE  _obj;

    static ID hash_id;
    static ID   lt_id;
    static ID   gt_id;
    static ID   eq_id;
    static ID   le_id;
    static ID   ge_id;

    static ID  pos_id;
    static ID  neg_id;
    static ID  inv_id;

    static ID  add_id;
    static ID  sub_id;
    static ID  mul_id;
    static ID  div_id;
    static ID  mod_id;

    static ID  and_id;
    static ID   or_id;
    static ID  xor_id;

    static ID  lshift_id;
    static ID  rshift_id;

    struct OpArgs
    {
      VALUE src;
      ID    id;
      int   nargs;
      VALUE target;
    };


  public:
    static void initialize()
    {
      if ( _hash == Qnil ) 
	{ 
	  _hash = rb_hash_new();
	  rb_gc_register_address( &_hash );
	}
    }

    // this function is never called.  Provided for symmetry only.
    static void cleanup()
    {
      rb_gc_unregister_address( &_hash );
    }

    GC_VALUE() : _obj( Qnil )
    {
    }

    GC_VALUE(const GC_VALUE& item) : _obj(item._obj)
    {
      GC_register();
    }
    
    GC_VALUE(VALUE obj) :_obj(obj)
    {
      GC_register();
    }
    
    ~GC_VALUE() 
    {
      GC_unregister();
    }
    
    GC_VALUE & operator=(const GC_VALUE& item) 
    {
      GC_unregister();
      _obj = item._obj;
      GC_register();
      return *this;
    }

    void GC_register()
    {
      if ( FIXNUM_P(_obj) || SPECIAL_CONST_P(_obj) || SYMBOL_P(_obj) ) 
	return;
      VALUE val = rb_hash_aref( _hash, _obj );
      unsigned n = FIXNUM_P(val) ? NUM2UINT(val) : 0;
      ++n;
      rb_hash_aset( _hash, _obj, INT2NUM(n) );
    }

    void GC_unregister()
    {
      if ( FIXNUM_P(_obj) || SPECIAL_CONST_P(_obj) || SYMBOL_P(_obj) ) 
	return;
      // this test should not be needed but I've noticed some very erratic
      // behavior of none being unregistered in some very rare situations.
      if ( BUILTIN_TYPE(_obj) == T_NONE ) return;

      VALUE val = rb_hash_aref( _hash, _obj );
      unsigned n = FIXNUM_P(val) ? NUM2UINT(val) : 1;
      --n;
      if ( n )
	rb_hash_aset( _hash, _obj, INT2NUM(n) );
      else
	rb_hash_delete( _hash, _obj );
    }
    
    operator VALUE() const
    {
      return _obj;
    }

    VALUE inspect() const
    {
      return rb_inspect(_obj);
    }

    VALUE to_s() const
    {
      return rb_inspect(_obj);
    }

    static VALUE swig_protect_funcall( VALUE p )
    {
      OpArgs* args = (OpArgs*) p;
      return rb_funcall( args->src, args->id, args->nargs, args->target );
    }


#define GC_VALUE_CMP( op_id, op, cmp, cmpval ) \
    bool op( const GC_VALUE& other ) const \
    { \
      if ( FIXNUM_P(_obj) && FIXNUM_P(other._obj) ) \
      { \
	return _obj cmp other._obj; \
      } \
      bool  res = false; \
      VALUE ret = Qnil; \
      SWIG_RUBY_THREAD_BEGIN_BLOCK; \
      if ( rb_respond_to( _obj, op_id ) == Qtrue ) \
	{ \
	  int status; \
	  OpArgs  args; \
          args.src    = _obj; \
	  args.id     = op_id; \
	  args.nargs  = 1; \
	  args.target = VALUE(other); \
	  ret = rb_protect( PROTECTFUNC(swig_protect_funcall), \
                            VALUE(&args), &status ); \
	} \
      if ( ret == Qnil ) { \
	VALUE a = rb_funcall(         _obj, hash_id, 0 ); \
	VALUE b = rb_funcall( VALUE(other), hash_id, 0 ); \
	res = a cmp b; \
      } \
      else \
	{ \
	  res = RTEST( ret ); \
	} \
      SWIG_RUBY_THREAD_END_BLOCK; \
      return res; \
    }


    GC_VALUE_CMP( eq_id, operator==, ==, == 0 )
    GC_VALUE_CMP( lt_id, operator<,  < , <  0 )
    GC_VALUE_CMP( le_id, operator<=, <=, <= 0 )
    GC_VALUE_CMP( gt_id, operator>,  > , >  0 )
    GC_VALUE_CMP( ge_id, operator>=, >=, >= 0 )
#undef GC_VALUE_CMP

    bool operator!=( const GC_VALUE& other )
    {
      return !(this->operator==(other));
    }

#define GC_VALUE_UNARY( proc_id, op ) \
    GC_VALUE op() const \
    { \
      VALUE ret = Qnil; \
      SWIG_RUBY_THREAD_BEGIN_BLOCK; \
      int status; \
      OpArgs  args; \
      args.src    = _obj; \
      args.id     = proc_id; \
      args.nargs  = 0; \
      args.target = Qnil; \
      ret = rb_protect( PROTECTFUNC(swig_protect_funcall), VALUE(&args), \
			&status ); \
      SWIG_RUBY_THREAD_END_BLOCK; \
      return ret; \
    }

    GC_VALUE_UNARY( pos_id, operator+ )
    GC_VALUE_UNARY( neg_id, operator- )
    GC_VALUE_UNARY( inv_id, operator~ )
#undef GC_VALUE_BINARY

#define GC_VALUE_BINARY( proc_id, op ) \
    GC_VALUE op( const GC_VALUE& other ) const \
    { \
      VALUE ret = Qnil; \
      SWIG_RUBY_THREAD_BEGIN_BLOCK; \
      int status; \
      OpArgs  args; \
      args.src    = _obj; \
      args.id     = proc_id; \
      args.nargs  = 1; \
      args.target = VALUE(other); \
      ret = rb_protect( PROTECTFUNC(swig_protect_funcall), VALUE(&args), \
			&status ); \
      SWIG_RUBY_THREAD_END_BLOCK; \
      return GC_VALUE(ret); \
    }

    GC_VALUE_BINARY( add_id, operator+ );
    GC_VALUE_BINARY( sub_id, operator- );
    GC_VALUE_BINARY( mul_id, operator* );
    GC_VALUE_BINARY( div_id, operator/ );
    GC_VALUE_BINARY( mod_id, operator% );
    
    GC_VALUE_BINARY( and_id, operator& );
    GC_VALUE_BINARY( xor_id, operator^ );
    GC_VALUE_BINARY(  or_id, operator| );

    GC_VALUE_BINARY( lshift_id, operator<< );
    GC_VALUE_BINARY( rshift_id, operator>> );
#undef GC_VALUE_BINARY

  };

  ID  GC_VALUE::hash_id = rb_intern("hash");
  ID  GC_VALUE::lt_id = rb_intern("<");
  ID  GC_VALUE::gt_id = rb_intern(">");
  ID  GC_VALUE::eq_id = rb_intern("==");
  ID  GC_VALUE::le_id = rb_intern("<=");
  ID  GC_VALUE::ge_id = rb_intern(">=");

  ID  GC_VALUE::pos_id = rb_intern("+@");
  ID  GC_VALUE::neg_id = rb_intern("-@");
  ID  GC_VALUE::inv_id = rb_intern("~");

  ID  GC_VALUE::add_id = rb_intern("+");
  ID  GC_VALUE::sub_id = rb_intern("-");
  ID  GC_VALUE::mul_id = rb_intern("*");
  ID  GC_VALUE::div_id = rb_intern("/");
  ID  GC_VALUE::mod_id = rb_intern("%");

  ID  GC_VALUE::and_id = rb_intern("&");
  ID  GC_VALUE::or_id  = rb_intern("|");
  ID  GC_VALUE::xor_id = rb_intern("^");

  ID  GC_VALUE::lshift_id = rb_intern("<<");
  ID  GC_VALUE::rshift_id = rb_intern(">>");

  VALUE GC_VALUE::_hash = Qnil;

  typedef GC_VALUE LANGUAGE_OBJ;

} // namespace swig

%}


%init {
  swig::GC_VALUE::initialize();
}



//
// Fragment that contains traits to properly deal with GC_VALUE.
// These functions may be invoked as a need of the from(), asval(),
// asptr() and as() template functors, usually used in %typemaps.
//
%fragment(SWIG_Traits_frag(swig::GC_VALUE),"header",fragment="StdTraits") {
namespace swig {
  template <>  struct traits<GC_VALUE > {
    typedef value_category category;
    static const char* type_name() { return "GC_VALUE"; }
  };
  
  template <>  struct traits_from<GC_VALUE> {
    typedef GC_VALUE value_type;
    static VALUE from(const value_type& val) {
      return static_cast<VALUE>(val);
    }
  };
  
  template <> 
  struct traits_check<GC_VALUE, value_category> {
    static bool check(GC_VALUE) {
      return true;
    }
  };
  
  template <>  struct traits_asval<GC_VALUE > {   
    typedef GC_VALUE value_type;
    static int asval(VALUE obj, value_type *val) {
      if (val) *val = obj;
      return SWIG_OK;
    }
  };
} // swig
} // %fragment(traits for swig::GC_VALUE)


#endif  // __cplusplus

