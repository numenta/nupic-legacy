%include <std_common.i>
%include <exception.i>
%include <std_alloc.i>

%{
#include <algorithm>
%}

// Common container methods

%define %std_container_methods(container...)
  container();
  container(const container&);

  bool empty() const;
  size_type size() const;
  void clear();

  void swap(container& v);

  allocator_type get_allocator() const;

  #ifdef SWIG_EXPORT_ITERATOR_METHODS
  class iterator;
  class reverse_iterator;
  class const_iterator;
  class const_reverse_iterator;

  iterator begin();
  iterator end();
  reverse_iterator rbegin();
  reverse_iterator rend();
  #endif

%enddef

// Common sequence

%define %std_sequence_methods_common(sequence)
  
  %std_container_methods(%arg(sequence));
  
  sequence(size_type size);
  void pop_back();
  
  void resize(size_type new_size);
  
  #ifdef SWIG_EXPORT_ITERATOR_METHODS
  iterator erase(iterator pos);
  iterator erase(iterator first, iterator last);
  #endif
  
%enddef


%define %std_sequence_methods(sequence)
  
  %std_sequence_methods_common(%arg(sequence));
  
  sequence(size_type size, const value_type& value);
  void push_back(const value_type& x);  

  const value_type& front() const;
  const value_type& back() const;
 
  void assign(size_type n, const value_type& x);

  void resize(size_type new_size, const value_type& x);
  
  #ifdef SWIG_EXPORT_ITERATOR_METHODS
  iterator insert(iterator pos, const value_type& x);
  void insert(iterator pos, size_type n, const value_type& x);
  #endif
  
%enddef

%define %std_sequence_methods_val(sequence...)
  
  %std_sequence_methods_common(%arg(sequence));
  
  sequence(size_type size, value_type value);
  void push_back(value_type x);  

  value_type front() const;
  value_type back() const;
 
  void assign(size_type n, value_type x);

  void resize(size_type new_size, value_type x);
  
  #ifdef SWIG_EXPORT_ITERATOR_METHODS
  iterator insert(iterator pos, value_type x);
  void insert(iterator pos, size_type n, value_type x);
  #endif
  
%enddef


//
// Ignore member methods for Type with no default constructor
//
%define %std_nodefconst_type(Type...)
%feature("ignore") std::vector<Type >::vector(size_type size);
%feature("ignore") std::vector<Type >::resize(size_type size);
%feature("ignore") std::deque<Type >::deque(size_type size);
%feature("ignore") std::deque<Type >::resize(size_type size);
%feature("ignore") std::list<Type >::list(size_type size);
%feature("ignore") std::list<Type >::resize(size_type size);
%enddef
