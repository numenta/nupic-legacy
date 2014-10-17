
#include <octave/version.h>
#ifndef OCTAVE_API_VERSION_NUMBER

  // Hack to distinguish between Octave 3.2 and earlier versions before OCTAVE_API_VERSION_NUMBER existed
  #define ComplexLU __ignore
  #include <octave/CmplxLU.h>
  #undef ComplexLU
  #ifdef octave_Complex_LU_h
  # define OCTAVE_API_VERSION_NUMBER 36
  #else
  # define OCTAVE_API_VERSION_NUMBER 37
  #endif

#endif

SWIGRUNTIME bool SWIG_check_num_args(const char *func_name, int num_args, int max_args, int min_args, int varargs) {
  if (num_args > max_args && !varargs)
    error("function %s takes at most %i arguments", func_name, max_args);
  else if (num_args < min_args)
    error("function %s requires at least %i arguments", func_name, min_args);
  else
    return true;
  return false;
}

SWIGRUNTIME octave_value_list *SWIG_Octave_AppendOutput(octave_value_list *ovl, const octave_value &ov) {
  ovl->append(ov);
  return ovl;
}

SWIGRUNTIME octave_value SWIG_ErrorType(int code) {
  switch (code) {
  case SWIG_MemoryError:
    return "SWIG_MemoryError";
  case SWIG_IOError:
    return "SWIG_IOError";
  case SWIG_RuntimeError:
    return "SWIG_RuntimeError";
  case SWIG_IndexError:
    return "SWIG_IndexError";
  case SWIG_TypeError:
    return "SWIG_TypeError";
  case SWIG_DivisionByZero:
    return "SWIG_DivisionByZero";
  case SWIG_OverflowError:
    return "SWIG_OverflowError";
  case SWIG_SyntaxError:
    return "SWIG_SyntaxError";
  case SWIG_ValueError:
    return "SWIG_ValueError";
  case SWIG_SystemError:
    return "SWIG_SystemError";
  case SWIG_AttributeError:
    return "SWIG_AttributeError";
  }
  return "SWIG unknown error";
}

SWIGRUNTIME octave_value SWIG_Error(int code, const char *msg) {
  octave_value type(SWIG_ErrorType(code));
  std::string r = msg;
  r += " (" + type.string_value() + ")";
  error(r.c_str());
  return octave_value(r);
}

#define SWIG_fail                                       goto fail

#define SWIG_Octave_ConvertPtr(obj, pptr, type, flags)  SWIG_Octave_ConvertPtrAndOwn(obj, pptr, type, flags, 0)
#define SWIG_ConvertPtr(obj, pptr, type, flags)         SWIG_Octave_ConvertPtr(obj, pptr, type, flags)
#define SWIG_ConvertPtrAndOwn(obj,pptr,type,flags,own)  SWIG_Octave_ConvertPtrAndOwn(obj, pptr, type, flags, own)
#define SWIG_ConvertPtr(obj, pptr, type, flags)         SWIG_Octave_ConvertPtr(obj, pptr, type, flags)
#define SWIG_NewPointerObj(ptr, type, flags)            SWIG_Octave_NewPointerObj(ptr, type, flags)
#define swig_owntype                                    int

#define SWIG_ConvertPacked(obj, ptr, sz, ty)            SWIG_Octave_ConvertPacked(obj, ptr, sz, ty)
#define SWIG_NewPackedObj(ptr, sz, type)                SWIG_Octave_NewPackedObj(ptr, sz, type)

#define SWIG_ConvertFunctionPtr(obj, pptr, type)        SWIG_ConvertPtr(obj, pptr, type, 0)
#define SWIG_NewFunctionPtrObj(ptr, type)               SWIG_NewPointerObj(ptr, type, 0)

#define SWIG_ConvertMember(obj, ptr, sz, ty)            SWIG_Octave_ConvertPacked(obj, ptr, sz, ty)
#define SWIG_NewMemberObj(ptr, sz, type)                SWIG_Octave_NewPackedObj(ptr, sz, type)

#define SWIG_GetModule(clientdata) SWIG_Octave_GetModule(clientdata)
#define SWIG_SetModule(clientdata, pointer) SWIG_Octave_SetModule(clientdata,pointer);
#define SWIG_MODULE_CLIENTDATA_TYPE void*

#define Octave_Error_Occurred() 0
#define SWIG_Octave_AddErrorMsg(msg) {;}

SWIGRUNTIME swig_module_info *SWIG_Octave_GetModule(void *clientdata);
SWIGRUNTIME void SWIG_Octave_SetModule(void *clientdata, swig_module_info *pointer);

// For backward compatibility only
#define SWIG_POINTER_EXCEPTION  0
#define SWIG_arg_fail(arg)      0

// Runtime API implementation

#include <map>
#include <vector>
#include <string>

typedef octave_value_list(*octave_func) (const octave_value_list &, int);
class octave_swig_type;

# define SWIG_DIRECTOR_CAST(ARG) dynamic_cast<Swig::Director *>(ARG)

namespace Swig {
  class Director;

  SWIGRUNTIME void swig_register_director(octave_swig_type *self, void *ptr, Director *d);
  SWIGRUNTIME void swig_director_destroyed(octave_swig_type *self, Director *d);
  SWIGRUNTIME void swig_director_set_self(Director *d, octave_swig_type *self);

  SWIGRUNTIME octave_base_value *swig_value_ref(octave_swig_type *ost);
  SWIGRUNTIME octave_swig_type *swig_value_deref(octave_value ov);
  SWIGRUNTIME octave_swig_type *swig_value_deref(const octave_base_value &ov);

  typedef std::map < void *, Director * > rtdir_map;

  SWIGINTERN rtdir_map* get_rtdir_map() {
    static swig_module_info *module = 0;
    if (!module)
      module = SWIG_GetModule(0);
    if (!module)
      return 0;
    if (!module->clientdata)
      module->clientdata = new rtdir_map;
    return (rtdir_map *) module->clientdata;
  }

  SWIGINTERNINLINE void set_rtdir(void *vptr, Director *d) {
    rtdir_map* rm = get_rtdir_map();
    if (rm)
      (*rm)[vptr] = d;
  }

  SWIGINTERNINLINE void erase_rtdir(void *vptr) {
    rtdir_map* rm = get_rtdir_map();
    if (rm)
      (*rm).erase(vptr);
  }

  SWIGINTERNINLINE Director *get_rtdir(void *vptr) {
    rtdir_map* rm = get_rtdir_map();
    if (!rm)
      return 0;
    rtdir_map::const_iterator pos = rm->find(vptr);
    Director *rtdir = (pos != rm->end())? pos->second : 0;
    return rtdir;
  }
}

  struct swig_octave_member {
    const char *name;
    octave_func method;
    octave_func get_method;
    octave_func set_method;
    int flags;			// 1 static, 2 global
    const char *doc;
    bool is_static() const {
      return flags &1;
    } bool is_global() const {
      return flags &2;
    }
  };

  struct swig_octave_class {
    const char *name;
    swig_type_info **type;
    int director;
    octave_func constructor;
    const char *constructor_doc;
    octave_func destructor;
    const swig_octave_member *members;
    const char **base_names;
    const swig_type_info **base;
  };

  // octave_swig_type plays the role of both the shadow class and the class 
  // representation within Octave, since there is no support for classes.
  //
  // These should really be decoupled, with the class support added to Octave
  // and the shadow class given by an m-file script. That would dramatically 
  // reduce the runtime complexity, and be more in line w/ other modules.

  class octave_swig_type:public octave_base_value {
    struct cpp_ptr {
      void *ptr;
      bool destroyed;
      cpp_ptr(void *_ptr):ptr(_ptr), destroyed(false) {
      }};
    typedef std::pair < const swig_type_info *, cpp_ptr > type_ptr_pair;

    mutable swig_module_info *module;

    const swig_type_info *construct_type;	// type of special type object
    std::vector < type_ptr_pair > types;	// our c++ base classes
    int own;			// whether we call c++ destructors when we die

    typedef std::pair < const swig_octave_member *, octave_value > member_value_pair;
    typedef std::map < std::string, member_value_pair > member_map;
    member_map members;
    bool always_static;

    const swig_octave_member *find_member(const swig_type_info *type, const std::string &name) {
      if (!type->clientdata)
	return 0;
      swig_octave_class *c = (swig_octave_class *) type->clientdata;
      const swig_octave_member *m;
      for (m = c->members; m->name; ++m)
	if (m->name == name)
	  return m;
      for (int j = 0; c->base_names[j]; ++j) {
	if (!c->base[j]) {
	  if (!module)
	    module = SWIG_GetModule(0);
	  assert(module);
	  c->base[j] = SWIG_MangledTypeQueryModule(module, module, c->base_names[j]);
	}
	if (!c->base[j])
	  return 0;
	if ((m = find_member(c->base[j], name)))
	  return m;
      }
      return 0;
    }

    member_value_pair *find_member(const std::string &name, bool insert_if_not_found) {
      member_map::iterator it = members.find(name);
      if (it != members.end())
	return &it->second;
      const swig_octave_member *m;
      for (unsigned int j = 0; j < types.size(); ++j)
	if ((m = find_member(types[j].first, name)))
	  return &members.insert(std::make_pair(name, std::make_pair(m, octave_value()))).first->second;
      if (!insert_if_not_found)
	return 0;
      return &members[name];
    }

    const swig_type_info *find_base(const std::string &name, const swig_type_info *base) {
      if (!base) {
	for (unsigned int j = 0; j < types.size(); ++j) {
	  assert(types[j].first->clientdata);
	  swig_octave_class *cj = (swig_octave_class *) types[j].first->clientdata;
	  if (cj->name == name)
	    return types[j].first;
	}
	return 0;
      }
      assert(base->clientdata);
      swig_octave_class *c = (swig_octave_class *) base->clientdata;
      for (int j = 0; c->base_names[j]; ++j) {
	if (!c->base[j]) {
	  if (!module)
	    module = SWIG_GetModule(0);
	  assert(module);
	  c->base[j] = SWIG_MangledTypeQueryModule(module, module, c->base_names[j]);
	}
	if (!c->base[j])
	  return 0;
	assert(c->base[j]->clientdata);
	swig_octave_class *cj = (swig_octave_class *) c->base[j]->clientdata;
	if (cj->name == name)
	  return c->base[j];
      }
      return 0;
    }

    void load_members(const swig_octave_class* c,member_map& out) const {
      for (const swig_octave_member *m = c->members; m->name; ++m) {
	if (out.find(m->name) == out.end())
	  out.insert(std::make_pair(m->name, std::make_pair(m, octave_value())));
      }
      for (int j = 0; c->base_names[j]; ++j) {
	if (!c->base[j]) {
	  if (!module)
	    module = SWIG_GetModule(0);
	  assert(module);
	  c->base[j] = SWIG_MangledTypeQueryModule(module, module, c->base_names[j]);
	}
	if (!c->base[j])
	  continue;
	assert(c->base[j]->clientdata);
	const swig_octave_class *cj =
	  (const swig_octave_class *) c->base[j]->clientdata;
	load_members(cj,out);
      }
    }

    void load_members(member_map& out) const {
      out=members;
      for (unsigned int j = 0; j < types.size(); ++j)
	if (types[j].first->clientdata)
	  load_members((const swig_octave_class *) types[j].first->clientdata, out);
    }

    octave_value_list member_invoke(member_value_pair *m, const octave_value_list &args, int nargout) {
      if (m->second.is_defined())
	return m->second.subsref("(", std::list < octave_value_list > (1, args), nargout);
      else if (m->first && m->first->method)
	return m->first->method(args, nargout);
      error("member not defined or not invocable");
      return octave_value_list();
    }

    bool dispatch_unary_op(const std::string &symbol, octave_value &ret) {
      member_value_pair *m = find_member(symbol, false);
      if (!m || m->first->is_static() || m->first->is_global())
	return false;
      octave_value_list args;
      args.append(as_value());
      octave_value_list argout(member_invoke(m, args, 1));
      if (argout.length() < 1)
	return false;
      ret = argout(0);
      return true;
    }

    bool dispatch_binary_op(const std::string &symbol, const octave_base_value &rhs, octave_value &ret) {
      member_value_pair *m = find_member(symbol, false);
      if (!m || m->first->is_static() || m->first->is_global())
	return false;
      octave_value_list args;
      args.append(as_value());
      args.append(make_value_hack(rhs));
      octave_value_list argout(member_invoke(m, args, 1));
      if (argout.length() < 1)
	return false;
      ret = argout(0);
      return true;
    }

    bool dispatch_index_op(const std::string &symbol, const octave_value_list &rhs, octave_value_list &ret) {
      member_value_pair *m = find_member(symbol, false);
      if (!m || m->first->is_static() || m->first->is_global())
	return false;
      octave_value_list args;
      args.append(as_value());
      args.append(rhs);
      octave_value_list argout(member_invoke(m, args, 1));
      if (argout.length() >= 1)
	ret = argout(0);
      return true;
    }

    octave_value_list member_deref(member_value_pair *m, const octave_value_list &args) {
      if (m->second.is_defined())
	return m->second;
      else if (m->first) {
	if (m->first->get_method)
	  return m->first->get_method(args, 1);
	else if (m->first->method)
	  return octave_value(new octave_builtin(m->first->method));
      }
      error("undefined member");
      return octave_value_list();
    }

    static octave_value make_value_hack(const octave_base_value &x) {
      ((octave_swig_type &) x).count++;
      return octave_value((octave_base_value *) &x);
    }

    octave_swig_type(const octave_swig_type &x);
    octave_swig_type &operator=(const octave_swig_type &rhs);
  public:

    octave_swig_type(void *_ptr = 0, const swig_type_info *_type = 0, int _own = 0,
		     bool _always_static = false)
      :	module(0), construct_type(_ptr ? 0 : _type), own(_own), 
      always_static(_always_static) {
      if (_type || _ptr)
	types.push_back(std::make_pair(_type, _ptr));
      if (_ptr) {
	Swig::Director *d = Swig::get_rtdir(_ptr);
	if (d)
	  Swig::swig_director_set_self(d, this);
      }
    }

    ~octave_swig_type() {
      if (own) {
	++count;
	for (unsigned int j = 0; j < types.size(); ++j) {
	  if (!types[j].first || !types[j].first->clientdata)
	    continue;
	  swig_octave_class *c = (swig_octave_class *) types[j].first->clientdata;
	  if (c->destructor && !types[j].second.destroyed && types[j].second.ptr) {
	    c->destructor(as_value(), 0);
	  }
	}
      }
      for (unsigned int j = 0; j < types.size(); ++j)
	Swig::erase_rtdir(types[j].second.ptr);
    }

    octave_value as_value() {
      ++count;
      return Swig::swig_value_ref(this);
    }

    void incref() {
      ++count;
    }

    void decref() {
      if (!--count)
	delete this;
    }

    long swig_this() const {
      if (!types.size())
	return (long) this;
      return (long) types[0].second.ptr;
    }
    const char* help_text() const {
      if (!types.size())
	return 0;
      if (!types[0].first->clientdata)
	return 0;
      swig_octave_class *c = (swig_octave_class *) types[0].first->clientdata;
      return c->constructor_doc;
    }

    std::string swig_type_name() const {
      // * need some way to manually name subclasses.
      // * eg optional first arg to subclass(), or named_subclass()
      std::string ret;
      for (unsigned int j = 0; j < types.size(); ++j) {
	if (j)
	  ret += "_";
	if (types[j].first->clientdata) {
	  swig_octave_class *c = (swig_octave_class *) types[j].first->clientdata;
	  ret += c->name;
	} else
	  ret += types[j].first->name;
      }
      return ret;
    }

    void merge(octave_swig_type &rhs) {
      rhs.own = 0;
      for (unsigned int j = 0; j < rhs.types.size(); ++j) {
	assert(!rhs.types[j].second.destroyed);
	Swig::Director *d = Swig::get_rtdir(rhs.types[j].second.ptr);
	if (d)
	  Swig::swig_director_set_self(d, this);
      }
      types.insert(types.end(), rhs.types.begin(), rhs.types.end());
      members.insert(rhs.members.begin(), rhs.members.end());
      rhs.types.clear();
      rhs.members.clear();
    }

    void install_global(bool global_load) {
      for (member_map::const_iterator it = members.begin(); it != members.end(); ++it) {
        bool is_global_op = (it->first.substr(0, strlen(SWIG_op_prefix)) == SWIG_op_prefix);
        bool is_func_defined = (it->second.first && it->second.first->method);
	if (is_func_defined && (is_global_op || global_load)) {
	  install_builtin_function(it->second.first->method, it->first,
				   it->second.first->doc ? it->second.first->doc : std::string());
        }
        octave_value global_val = is_global_op ? make_fcn_handle(it->first) : it->second.second;
	if (global_val.is_defined() && (is_global_op || global_load)) {
#if OCTAVE_API_VERSION_NUMBER<37
	  link_to_global_variable(curr_sym_tab->lookup(it->first, true));
#else 
	  symbol_table::varref(it->first);
	  symbol_table::mark_global(it->first);
#endif
	  set_global_value(it->first, global_val);
	  
#if OCTAVE_API_VERSION_NUMBER<37
	  octave_swig_type *ost = Swig::swig_value_deref(global_val);
	  if (ost) {
	    const char* h = ost->help_text();
	    if (h) {
	      symbol_record *sr = global_sym_tab->lookup (it->first, true);
	      sr->document(h);
	    }
	  }
#endif
	}
      }
    }

    void *cast(swig_type_info *type, int *_own, int flags) {
      if (_own)
	*_own = own;
      if (flags &SWIG_POINTER_DISOWN)
	own = 0;
      if (!type && types.size())
	return types[0].second.ptr;
      for (unsigned int j = 0; j < types.size(); ++j)
	if (type == types[j].first)
	  return types[j].second.ptr;
      for (unsigned int j = 0; j < types.size(); ++j) {
	swig_cast_info *tc = SWIG_TypeCheck(types[j].first->name, type);
	if (!tc)
	  continue;
	int newmemory = 0;
	void *vptr = SWIG_TypeCast(tc, types[j].second.ptr, &newmemory);
	assert(!newmemory);	// newmemory handling not yet implemented
	return vptr;
      }
      return 0;
    }

    bool is_owned() const {
      return own;
    }

    void director_destroyed(Swig::Director *d) {
      bool found = false;
      for (unsigned int j = 0; j < types.size(); ++j) {
	Swig::Director *dj = Swig::get_rtdir(types[j].second.ptr);
	if (dj == d) {
	  types[j].second.destroyed = true;
	  found = true;
	}
      }
      assert(found);
    }

    void assign(const std::string &name, const octave_value &ov) {
      members[name] = std::make_pair((const swig_octave_member *) 0, ov);
    }

    void assign(const std::string &name, const swig_octave_member *m) {
      members[name] = std::make_pair(m, octave_value());
    }

    octave_base_value *clone() const {
      // pass-by-value is probably not desired, and is harder;
      // requires calling copy constructors of contained types etc.
      assert(0);
      *(int *) 0 = 0;
      return 0;
    }

    octave_base_value *empty_clone() const {
      return new octave_swig_type();
    }

    bool is_defined() const {
      return true;
    }

    virtual bool is_map() const {
      return true;
    }

    virtual octave_value subsref(const std::string &ops, const std::list < octave_value_list > &idx) {
      octave_value_list ovl = subsref(ops, idx, 1);
      return ovl.length()? ovl(0) : octave_value();
    }

    virtual octave_value_list subsref(const std::string &ops, const std::list < octave_value_list > &idx, int nargout) {
      assert(ops.size() > 0);
      assert(ops.size() == idx.size());

      std::list < octave_value_list >::const_iterator idx_it = idx.begin();
      int skip = 0;
      octave_value_list sub_ovl;

      // constructor invocation
      if (ops[skip] == '(' && construct_type) {
	assert(construct_type->clientdata);
	swig_octave_class *c = (swig_octave_class *) construct_type->clientdata;
	if (!c->constructor) {
	  error("cannot create instance");
	  return octave_value_list();
	}
	octave_value_list args;
	if (c->director)
	  args.append(Swig::swig_value_ref(new octave_swig_type(this, 0, 0)));
	args.append(*idx_it++);
	++skip;
	sub_ovl = c->constructor(args, nargout);
      }
      // member dereference or invocation
      else if (ops[skip] == '.') {
	std::string subname;
	const swig_type_info *base = 0;	// eg, a.base.base_cpp_mem
	for (;;) {
	  octave_value_list subname_ovl(*idx_it++);
	  ++skip;
	  assert(subname_ovl.length() == 1 && subname_ovl(0).is_string());
	  subname = subname_ovl(0).string_value();

	  const swig_type_info *next_base = find_base(subname, base);
	  if (!next_base || skip >= (int) ops.size() || ops[skip] != '.')
	    break;
	  base = next_base;
	}

	member_value_pair tmp, *m = &tmp;
	if (!base || !(m->first = find_member(base, subname)))
	  m = find_member(subname, false);
	if (!m) {
	  error("member not found");
	  return octave_value_list();
	}

	octave_value_list args;
	if (!always_static &&
	    (!m->first || (!m->first->is_static() && !m->first->is_global())))
	  args.append(as_value());
	if (skip < (int) ops.size() && ops[skip] == '(' && 
	    ((m->first && m->first->method) || m->second.is_function() || 
	     m->second.is_function_handle())) {
	  args.append(*idx_it++);
	  ++skip;
	  sub_ovl = member_invoke(m, args, nargout);
	} else {
	  sub_ovl = member_deref(m, args);
	}
      }
      // index operator
      else {
	if (ops[skip] == '(' || ops[skip] == '{') {
	  const char *op_name = ops[skip] == '(' ? "__paren__" : "__brace__";
	  octave_value_list args;
	  args.append(*idx_it++);
	  ++skip;
	  if (!dispatch_index_op(op_name, args, sub_ovl)) {
	    error("error evaluating index operator");
	    return octave_value_list();
	  }
	} else {
	  error("unsupported subsref");
	  return octave_value_list();
	}
      }

      if (skip >= (int) ops.size())
	return sub_ovl;
      if (sub_ovl.length() < 1) {
	error("bad subs ref");
	return octave_value_list();
      }
      return sub_ovl(0).next_subsref(nargout, ops, idx, skip);
    }

    octave_value subsasgn(const std::string &ops, const std::list < octave_value_list > &idx, const octave_value &rhs) {
      assert(ops.size() > 0);
      assert(ops.size() == idx.size());

      std::list < octave_value_list >::const_iterator idx_it = idx.begin();
      int skip = 0;

      if (ops.size() > 1) {
	std::list < octave_value_list >::const_iterator last = idx.end();
	--last;
	std::list < octave_value_list > next_idx(idx.begin(), last);
	octave_value next_ov = subsref(ops.substr(0, ops.size() - 1), next_idx);
	next_ov.subsasgn(ops.substr(ops.size() - 1), std::list < octave_value_list > (1, *last), rhs);
      }

      else if (ops[skip] == '(' || ops[skip] == '{') {
	const char *op_name = ops[skip] == '(' ? "__paren_asgn__" : "__brace_asgn__";
	member_value_pair *m = find_member(op_name, false);
	if (m) {
	  octave_value_list args;
	  args.append(as_value());
	  args.append(*idx_it);
	  args.append(rhs);
	  member_invoke(m, args, 1);
	} else
	  error("%s member not found", op_name);
      }

      else if (ops[skip] == '.') {
	octave_value_list subname_ovl(*idx_it++);
	++skip;
	assert(subname_ovl.length() == 1 &&subname_ovl(0).is_string());
	std::string subname = subname_ovl(0).string_value();

	member_value_pair *m = find_member(subname, true);
	if (!m->first || !m->first->set_method) {
	  m->first = 0;
	  m->second = rhs;
	} else if (m->first->set_method) {
	  octave_value_list args;
	  if (!m->first->is_static() && !m->first->is_global())
	    args.append(as_value());
	  args.append(rhs);
	  m->first->set_method(args, 1);
	} else
	  error("member not assignable");
      } else
	error("unsupported subsasgn");

      return as_value();
    }

    virtual bool is_string() const {
      octave_swig_type *nc_this = const_cast < octave_swig_type *>(this);
      return !!nc_this->find_member("__str__", false);
    }

    virtual std::string string_value(bool force = false) const {
      octave_swig_type *nc_this = const_cast < octave_swig_type *>(this);
      member_value_pair *m = nc_this->find_member("__str__", false);
      if (!m) {
	error("__str__ method not defined");
	return std::string();
      }
      octave_value_list outarg = nc_this->member_invoke(m, octave_value_list(nc_this->as_value()), 1);
      if (outarg.length() < 1 || !outarg(0).is_string()) {
	error("__str__ method did not return a string");
	return std::string();
      }
      return outarg(0).string_value();
    }

#if OCTAVE_API_VERSION_NUMBER >= 40
    virtual octave_map map_value() const {
      return octave_map();
    }
#else
    virtual Octave_map map_value() const {
      return Octave_map();
    }
#endif

    virtual string_vector map_keys() const {
      member_map tmp;
      load_members(tmp);

      string_vector keys(tmp.size());
      int k = 0;
      for (member_map::iterator it = tmp.begin(); it != tmp.end(); ++it)
	keys(k++) = it->first;

      return keys;
    }

    virtual bool save_ascii (std::ostream& os) {
      return true;
    }

    virtual bool load_ascii (std::istream& is) {
      return true;
    }

    virtual bool save_binary (std::ostream& os, bool& save_as_floats) {
      return true;
    }

    virtual bool load_binary (std::istream& is, bool swap, 
			      oct_mach_info::float_format fmt) {
      return true;
    }

#if defined (HAVE_HDF5)
    virtual bool
      save_hdf5 (hid_t loc_id, const char *name, bool save_as_floats) {
      return true;
    }

    virtual bool
      load_hdf5 (hid_t loc_id, const char *name, bool have_h5giterate_bug) {
      return true;
    }
#endif

    virtual octave_value convert_to_str(bool pad = false, bool force = false, char type = '"') const {
      return string_value();
    }

    virtual octave_value convert_to_str_internal(bool pad, bool force, char type) const {
      return string_value();
    }

    static bool dispatch_global_op(const std::string &symbol, const octave_value_list &args, octave_value &ret) {
      // we assume that SWIG_op_prefix-prefixed functions are installed in global namespace
      // (rather than any module namespace).

      octave_value fcn = get_global_value(symbol, true);
      if (!fcn.is_function() && !fcn.is_function_handle())
	return false;
      ret = fcn.subsref("(", std::list < octave_value_list > (1, args));
      return true;
    }

    static octave_value dispatch_unary_op(const octave_base_value &x, const char *op_name) {
      octave_swig_type *ost = Swig::swig_value_deref(x);
      assert(ost);

      octave_value ret;
      if (ost->dispatch_unary_op(std::string("__") + op_name + std::string("__"), ret))
	return ret;
      std::string symbol = SWIG_op_prefix + ost->swig_type_name() + "_" + op_name;
      octave_value_list args;
      args.append(make_value_hack(x));
      if (dispatch_global_op(symbol, args, ret))
	return ret;

      error("could not dispatch unary operator");
      return octave_value();
    }

    static octave_value dispatch_binary_op(const octave_base_value &lhs, const octave_base_value &rhs, const char *op_name) {
      octave_swig_type *lhs_ost = Swig::swig_value_deref(lhs);
      octave_swig_type *rhs_ost = Swig::swig_value_deref(rhs);

      octave_value ret;
      if (lhs_ost && lhs_ost->dispatch_binary_op(std::string("__") + op_name + std::string("__"), rhs, ret))
	return ret;
      if (rhs_ost) {
        if (strlen(op_name) == 2  && (op_name[1] == 't' || op_name[1] == 'e')) {
          if (op_name[0] == 'l' && rhs_ost->dispatch_binary_op(std::string("__g") + op_name[1] + std::string("__"), lhs, ret))
            return ret;
          if (op_name[0] == 'g' && rhs_ost->dispatch_binary_op(std::string("__l") + op_name[1] + std::string("__"), lhs, ret))
            return ret;
        }
        if (rhs_ost->dispatch_binary_op(std::string("__r") + op_name + std::string("__"), lhs, ret))
          return ret;
      }

      std::string symbol;
      octave_value_list args;
      args.append(make_value_hack(lhs));
      args.append(make_value_hack(rhs));

      symbol = SWIG_op_prefix;
      symbol += lhs_ost ? lhs_ost->swig_type_name() : lhs.type_name();
      symbol += "_";
      symbol += op_name;
      symbol += "_";
      symbol += rhs_ost ? rhs_ost->swig_type_name() : rhs.type_name();
      if (dispatch_global_op(symbol, args, ret))
	return ret;

      symbol = SWIG_op_prefix;
      symbol += lhs_ost ? lhs_ost->swig_type_name() : lhs.type_name();
      symbol += "_";
      symbol += op_name;
      symbol += "_";
      symbol += "any";
      if (dispatch_global_op(symbol, args, ret))
	return ret;

      symbol = SWIG_op_prefix;
      symbol += "any";
      symbol += "_";
      symbol += op_name;
      symbol += "_";
      symbol += rhs_ost ? rhs_ost->swig_type_name() : rhs.type_name();
      if (dispatch_global_op(symbol, args, ret))
	return ret;

      error("could not dispatch binary operator");
      return octave_value();
    }

    void print(std::ostream &os, bool pr_as_read_syntax = false) const {
      if (is_string()) {
	os << string_value();
	return;
      }

      member_map tmp;
      load_members(tmp);

      indent(os);
      os << "{"; newline(os);
      increment_indent_level();
      for (unsigned int j = 0; j < types.size(); ++j) {
        indent(os);
	if (types[j].first->clientdata) {
	  const swig_octave_class *c = (const swig_octave_class *) types[j].first->clientdata;
	  os << c->name << ", ptr = " << types[j].second.ptr; newline(os);
	} else {
	  os << types[j].first->name << ", ptr = " << types[j].second.ptr; newline(os);
	}
      }
      for (member_map::const_iterator it = tmp.begin(); it != tmp.end(); ++it) {
        indent(os);
	if (it->second.first) {
	  const char *objtype = it->second.first->method ? "method" : "variable";
	  const char *modifier = (it->second.first->flags &1) ? "static " : (it->second.first->flags &2) ? "global " : "";
	  os << it->second.first->name << " (" << modifier << objtype << ")"; newline(os);
	  assert(it->second.first->name == it->first);
	} else {
	  os << it->first; newline(os);
	}
      }
      decrement_indent_level();
      indent(os);
      os << "}"; newline(os);
    }
  };

  // Octave tries hard to preserve pass-by-value semantics. Eg, assignments
  // will call clone() via make_unique() if there is more than one outstanding 
  // reference to the lhs, and forces the clone's reference count to 1 
  // (so you can't just increment your own count and return this).
  //
  // One way to fix this (without modifying Octave) is to add a level of
  // indirection such that clone copies ref-counted pointer and we keep 
  // pass-by-ref semantics (which are more natural/expected for C++ bindings).
  //
  // Supporting both pass-by-{ref,value} and toggling via %feature/option 
  // might be nice.

  class octave_swig_ref:public octave_base_value {
    octave_swig_type *ptr;
  public:
    octave_swig_ref(octave_swig_type *_ptr = 0)
      :ptr(_ptr) { }

    ~octave_swig_ref()
      { if (ptr) ptr->decref(); }

    octave_swig_type *get_ptr() const
      { return ptr; }

    octave_base_value *clone() const
      { if (ptr) ptr->incref(); return new octave_swig_ref(ptr); }

    octave_base_value *empty_clone() const
      { return new octave_swig_ref(0); }

    bool is_defined() const
      { return ptr->is_defined(); }

    virtual bool is_map() const 
      { return ptr->is_map(); }

    virtual octave_value subsref(const std::string &ops, const std::list < octave_value_list > &idx) 
      { return ptr->subsref(ops, idx); }

    virtual octave_value_list subsref(const std::string &ops, const std::list < octave_value_list > &idx, int nargout)
      { return ptr->subsref(ops, idx, nargout); }

    octave_value subsasgn(const std::string &ops, const std::list < octave_value_list > &idx, const octave_value &rhs)
      { return ptr->subsasgn(ops, idx, rhs); }

    virtual bool is_string() const 
      { return ptr->is_string(); }

    virtual std::string string_value(bool force = false) const 
      { return ptr->string_value(force); }

#if OCTAVE_API_VERSION_NUMBER >= 40
    virtual octave_map map_value() const
      { return ptr->map_value(); }
#else
    virtual Octave_map map_value() const
      { return ptr->map_value(); }
#endif

    virtual string_vector map_keys() const
      { return ptr->map_keys(); }

    virtual bool save_ascii (std::ostream& os)
      { return ptr->save_ascii(os); }

    virtual bool load_ascii (std::istream& is)
      { return ptr->load_ascii(is); }

    virtual bool save_binary (std::ostream& os, bool& save_as_floats)
      { return ptr->save_binary(os, save_as_floats); }

    virtual bool load_binary (std::istream& is, bool swap, 
			      oct_mach_info::float_format fmt)
      { return ptr->load_binary(is, swap, fmt); }

#if defined (HAVE_HDF5)
    virtual bool
      save_hdf5 (hid_t loc_id, const char *name, bool save_as_floats)
      { return ptr->save_hdf5(loc_id, name, save_as_floats); }

    virtual bool
      load_hdf5 (hid_t loc_id, const char *name, bool have_h5giterate_bug)
      { return ptr->load_hdf5(loc_id, name, have_h5giterate_bug); }
#endif

    virtual octave_value convert_to_str(bool pad = false, bool force = false, char type = '"') const
      { return ptr->convert_to_str(pad, force, type); }

    virtual octave_value convert_to_str_internal(bool pad, bool force, char type) const
      { return ptr->convert_to_str_internal(pad, force, type); }

    void print(std::ostream &os, bool pr_as_read_syntax = false) const
      { return ptr->print(os, pr_as_read_syntax); }

  private:
    DECLARE_OCTAVE_ALLOCATOR;
    DECLARE_OV_TYPEID_FUNCTIONS_AND_DATA;
  };
  DEFINE_OCTAVE_ALLOCATOR(octave_swig_ref);
  DEFINE_OV_TYPEID_FUNCTIONS_AND_DATA(octave_swig_ref, "swig_ref", "swig_ref");

  class octave_swig_packed:public octave_base_value {
    swig_type_info *type;
    std::vector < char > buf;
  public:

    octave_swig_packed(swig_type_info *_type = 0, const void *_buf = 0, size_t _buf_len = 0)
      :	type(_type), buf((const char*)_buf, (const char*)_buf + _buf_len) {
    }

    bool copy(swig_type_info *outtype, void *ptr, size_t sz) const {
      if (outtype && outtype != type)
	return false;
      assert(sz <= buf.size());
      std::copy(buf.begin(), buf.begin()+sz, (char*)ptr);
      return true;
    }

    octave_base_value *clone() const {
      return new octave_swig_packed(*this);
    }

    octave_base_value *empty_clone() const {
      return new octave_swig_packed();
    }

    bool is_defined() const {
      return true;
    }

    void print(std::ostream &os, bool pr_as_read_syntax = false) const {
      indent(os);
      os << "swig packed type: name = " << (type ? type->name : std::string()) << ", len = " << buf.size(); newline(os);
    }


    virtual bool save_ascii (std::ostream& os) {
      return true;
    }

    virtual bool load_ascii (std::istream& is) {
      return true;
    }

    virtual bool save_binary (std::ostream& os, bool& save_as_floats) {
      return true;
    }

    virtual bool load_binary (std::istream& is, bool swap, 
			      oct_mach_info::float_format fmt) {
      return true;
    }

#if defined (HAVE_HDF5)
    virtual bool
      save_hdf5 (hid_t loc_id, const char *name, bool save_as_floats) {
      return true;
    }

    virtual bool
      load_hdf5 (hid_t loc_id, const char *name, bool have_h5giterate_bug) {
      return true;
    }
#endif

  private:
    DECLARE_OCTAVE_ALLOCATOR;
    DECLARE_OV_TYPEID_FUNCTIONS_AND_DATA;
  };
  DEFINE_OCTAVE_ALLOCATOR(octave_swig_packed);
  DEFINE_OV_TYPEID_FUNCTIONS_AND_DATA(octave_swig_packed, "swig_packed", "swig_packed");

  static octave_value_list octave_set_immutable(const octave_value_list &args, int nargout) {
    error("attempt to set immutable member variable");
    return octave_value_list();
  }

  struct octave_value_ref {
    const octave_value_list &ovl;
    int j;

    octave_value_ref(const octave_value_list &_ovl, int _j)
      :ovl(_ovl), j(_j) { }

    operator  octave_value() const {
      return ovl(j);
    }

    octave_value operator*() const {
      return ovl(j);
    }
  };

  octave_value_list swig_subclass(const octave_value_list &args, int nargout) {
    octave_swig_type *top = new octave_swig_type;
    for (int j = 0; j < args.length(); ++j) {
      if (args(j).type_id() == octave_swig_ref::static_type_id()) {
	octave_swig_ref *osr = static_cast < octave_swig_ref *>(args(j).internal_rep());
	octave_swig_type *ost = osr->get_ptr();
	if (!ost->is_owned()) {
	  error("cannot subclass object not constructed on octave side");
	  return octave_value_list();
	}
	top->merge(*ost);
      } else if (args(j).is_function_handle()) {
	top->assign(args(j).fcn_handle_value()->fcn_name(), args(j));
      } else if (args(j).is_string()) {
	if (j + 1 >= args.length()) {
	  error("member assignments must be of string,value form");
	  return octave_value_list();
	}
	top->assign(args(j).string_value(), args(j + 1));
	++j;
      } else {
	error("invalid arguments to subclass");
	return octave_value_list();
      }
    }
    return octave_value(Swig::swig_value_ref(top));
  }

  octave_value_list swig_type(const octave_value_list &args, int nargout) {
    if (args.length() != 1) {
      error("swig_typeinfo must be called with only a single object");
      return octave_value_list();
    }
    octave_swig_type *ost = Swig::swig_value_deref(args(0));
    if (!ost) {
      error("object is not a swig_ref");
      return octave_value_list();
    }
    return octave_value(ost->swig_type_name());
  }

  octave_value_list swig_typequery(const octave_value_list &args, int nargout) {
    if (args.length() != 1 || !args(0).is_string()) {
      error("swig_typeinfo must be called with single string argument");
      return octave_value_list();
    }
    swig_module_info *module = SWIG_GetModule(0);
    swig_type_info *type = SWIG_TypeQueryModule(module, module, args(0).string_value().c_str());
    if (!type)
      return octave_value("<unknown>");
    return octave_value(type->name);
  }

  octave_value_list swig_this(const octave_value_list &args, int nargout) {
    if (args.length() != 1) {
      error("swig_typeinfo must be called with only a single object");
      return octave_value_list();
    }
    if (args(0).is_matrix_type() && args(0).rows() == 0 && args(0).columns() == 0)
      return octave_value(octave_uint64(0));
    octave_swig_type *ost = Swig::swig_value_deref(args(0));
    if (!ost) {
      error("object is not a swig_ref");
      return octave_value_list();
    }
    return octave_value(octave_uint64((unsigned long long) ost->swig_this()));
  }

#define SWIG_DIRECTORS

namespace Swig {
  class Director {
    octave_swig_type *self;
    bool swig_disowned;

    Director(const Director &x);
    Director &operator=(const Director &rhs);
  public:

    Director(void *vptr):self(0), swig_disowned(false) {
      set_rtdir(vptr, this);
    }

    ~Director() {
      swig_director_destroyed(self, this);
      if (swig_disowned)
	self->decref();
    }

    void swig_set_self(octave_swig_type *new_self) {
      assert(!swig_disowned);
      self = new_self;
    }

    octave_swig_type *swig_get_self() const {
      return self;
    }

    void swig_disown() {
      if (swig_disowned)
	return;
      swig_disowned = true;
      self->incref();
    }
  };

  struct DirectorTypeMismatchException {
    static void raise(const char *msg) {
      // ... todo
      throw(DirectorTypeMismatchException());
    }

    static void raise(const octave_value &ov, const char *msg) {
      // ... todo
      raise(msg);
    }
  };
  struct DirectorPureVirtualException {
    static void raise(const char *msg) {
      // ... todo
      throw(DirectorPureVirtualException());
    }

    static void raise(const octave_value &ov, const char *msg) {
      // ... todo
      raise(msg);
    }
  };

}

  SWIGRUNTIME void swig_acquire_ownership(void *vptr) {
    //  assert(0);
    // ... todo
  }

  SWIGRUNTIME void swig_acquire_ownership_array(void *vptr) {
    //  assert(0);
    // ... todo
  }

  SWIGRUNTIME void swig_acquire_ownership_obj(void *vptr, int own) {
    //  assert(0);
    // ... todo
  }

  namespace Swig {
    SWIGRUNTIME void swig_director_destroyed(octave_swig_type *self, Director *d) {
      self->director_destroyed(d);
    }

    SWIGRUNTIME void swig_director_set_self(Director *d, octave_swig_type *self) {
      d->swig_set_self(self);
    }

    SWIGRUNTIME octave_base_value *swig_value_ref(octave_swig_type *ost) {
      return new octave_swig_ref(ost);
    }

    SWIGRUNTIME octave_swig_type *swig_value_deref(octave_value ov) {
      if (ov.is_cell() && ov.rows() == 1 && ov.columns() == 1)
	ov = ov.cell_value()(0);
      return swig_value_deref(*ov.internal_rep());
    }

    SWIGRUNTIME octave_swig_type *swig_value_deref(const octave_base_value &ov) {
      if (ov.type_id() != octave_swig_ref::static_type_id())
	return 0;
      const octave_swig_ref *osr = static_cast < const octave_swig_ref *>(&ov);
      return osr->get_ptr();
    }

  }

#define swig_unary_op(name) \
SWIGRUNTIME octave_value swig_unary_op_##name(const octave_base_value &x) { \
  return octave_swig_type::dispatch_unary_op(x,#name); \
}
#define swig_binary_op(name) \
SWIGRUNTIME octave_value swig_binary_op_##name(const octave_base_value&lhs,const octave_base_value &rhs) { \
  return octave_swig_type::dispatch_binary_op(lhs,rhs,#name); \
}
#define swigreg_unary_op(name) \
if (!octave_value_typeinfo::lookup_unary_op(octave_value::op_##name,tid)) \
octave_value_typeinfo::register_unary_op(octave_value::op_##name,tid,swig_unary_op_##name);
#define swigreg_binary_op(name) \
if (!octave_value_typeinfo::lookup_binary_op(octave_value::op_##name,tid1,tid2)) \
octave_value_typeinfo::register_binary_op(octave_value::op_##name,tid1,tid2,swig_binary_op_##name);

  swig_unary_op(not);
  swig_unary_op(uplus);
  swig_unary_op(uminus);
  swig_unary_op(transpose);
  swig_unary_op(hermitian);
  swig_unary_op(incr);
  swig_unary_op(decr);

  swig_binary_op(add);
  swig_binary_op(sub);
  swig_binary_op(mul);
  swig_binary_op(div);
  swig_binary_op(pow);
  swig_binary_op(ldiv);
  swig_binary_op(lshift);
  swig_binary_op(rshift);
  swig_binary_op(lt);
  swig_binary_op(le);
  swig_binary_op(eq);
  swig_binary_op(ge);
  swig_binary_op(gt);
  swig_binary_op(ne);
  swig_binary_op(el_mul);
  swig_binary_op(el_div);
  swig_binary_op(el_pow);
  swig_binary_op(el_ldiv);
  swig_binary_op(el_and);
  swig_binary_op(el_or);

  SWIGRUNTIME void SWIG_InstallUnaryOps(int tid) {
    swigreg_unary_op(not);
    swigreg_unary_op(uplus);
    swigreg_unary_op(uminus);
    swigreg_unary_op(transpose);
    swigreg_unary_op(hermitian);
    swigreg_unary_op(incr);
    swigreg_unary_op(decr);
  }
  SWIGRUNTIME void SWIG_InstallBinaryOps(int tid1, int tid2) {
    swigreg_binary_op(add);
    swigreg_binary_op(sub);
    swigreg_binary_op(mul);
    swigreg_binary_op(div);
    swigreg_binary_op(pow);
    swigreg_binary_op(ldiv);
    swigreg_binary_op(lshift);
    swigreg_binary_op(rshift);
    swigreg_binary_op(lt);
    swigreg_binary_op(le);
    swigreg_binary_op(eq);
    swigreg_binary_op(ge);
    swigreg_binary_op(gt);
    swigreg_binary_op(ne);
    swigreg_binary_op(el_mul);
    swigreg_binary_op(el_div);
    swigreg_binary_op(el_pow);
    swigreg_binary_op(el_ldiv);
    swigreg_binary_op(el_and);
    swigreg_binary_op(el_or);
  }
  SWIGRUNTIME void SWIG_InstallOps(int tid) {
    // here we assume that tid are conseq integers increasing from zero, and 
    // that our tid is the last one. might be better to have explicit string 
    // list of types we should bind to, and use lookup_type to resolve their tid.

    SWIG_InstallUnaryOps(tid);
    SWIG_InstallBinaryOps(tid, tid);
    for (int j = 0; j < tid; ++j) {
      SWIG_InstallBinaryOps(j, tid);
      SWIG_InstallBinaryOps(tid, j);
    }
  }

SWIGRUNTIME octave_value SWIG_Octave_NewPointerObj(void *ptr, swig_type_info *type, int flags) {
  int own = (flags &SWIG_POINTER_OWN) ? SWIG_POINTER_OWN : 0;

  Swig::Director *d = Swig::get_rtdir(ptr);
  if (d && d->swig_get_self())
    return d->swig_get_self()->as_value();
  return Swig::swig_value_ref(new octave_swig_type(ptr, type, own));
}

SWIGRUNTIME int SWIG_Octave_ConvertPtrAndOwn(octave_value ov, void **ptr, swig_type_info *type, int flags, int *own) {
  if (ov.is_cell() && ov.rows() == 1 && ov.columns() == 1)
    ov = ov.cell_value()(0);
  if (!ov.is_defined() ||
      (ov.is_matrix_type() && ov.rows() == 0 && ov.columns() == 0) ) {
    if (ptr)
      *ptr = 0;
    return SWIG_OK;
  }
  if (ov.type_id() != octave_swig_ref::static_type_id())
    return SWIG_ERROR;
  octave_swig_ref *osr = static_cast < octave_swig_ref *>(ov.internal_rep());
  octave_swig_type *ost = osr->get_ptr();
  void *vptr = ost->cast(type, own, flags);
  if (!vptr)
    return SWIG_ERROR;
  if (ptr)
    *ptr = vptr;
  return SWIG_OK;
}

SWIGRUNTIME octave_value SWIG_Octave_NewPackedObj(void *ptr, size_t sz, swig_type_info *type) {
  return new octave_swig_packed(type, (char *) ptr, sz);
}

SWIGRUNTIME int SWIG_Octave_ConvertPacked(const octave_value &ov, void *ptr, size_t sz, swig_type_info *type) {
  if (!ov.is_defined())
    return SWIG_ERROR;
  if (ov.type_id() != octave_swig_packed::static_type_id())
    return SWIG_ERROR;
  octave_swig_packed *ost = static_cast < octave_swig_packed *>(ov.internal_rep());
  return ost->copy(type, (char *) ptr, sz) ? SWIG_OK : SWIG_ERROR;
}

void SWIG_Octave_SetConstant(octave_swig_type *module_ns, const std::string &name, const octave_value &ov) {
  module_ns->assign(name, ov);
}

SWIGRUNTIME swig_module_info *SWIG_Octave_GetModule(void *clientdata) {
  octave_value ov = get_global_value("__SWIG_MODULE__" SWIG_TYPE_TABLE_NAME SWIG_RUNTIME_VERSION, true);
  if (!ov.is_defined() ||
      ov.type_id() != octave_swig_packed::static_type_id())
    return 0;
  const octave_swig_packed* osp = 
    static_cast < const octave_swig_packed *> (ov.internal_rep());
  swig_module_info *pointer = 0;
  osp->copy(0, &pointer, sizeof(swig_module_info *));
  return pointer;
}

SWIGRUNTIME void SWIG_Octave_SetModule(void *clientdata, swig_module_info *pointer) {
  octave_value ov = new octave_swig_packed(0, &pointer, sizeof(swig_module_info *));
  const char *module_var = "__SWIG_MODULE__" SWIG_TYPE_TABLE_NAME SWIG_RUNTIME_VERSION;
#if OCTAVE_API_VERSION_NUMBER<37
  link_to_global_variable(curr_sym_tab->lookup(module_var, true));
#else
  symbol_table::varref(module_var);
  symbol_table::mark_global(module_var);
#endif
  set_global_value(module_var, ov);
}
