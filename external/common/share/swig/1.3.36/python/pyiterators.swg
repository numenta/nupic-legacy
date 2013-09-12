/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * pyiterators.swg
 *
 * Implement a python 'output' iterator for Python 2.2 or higher.
 *
 * Users can derive form the PySwigIterator to implement their
 * own iterators. As an example (real one since we use it for STL/STD
 * containers), the template PySwigIterator_T does the
 * implementation for genereic C++ iterators.
 * ----------------------------------------------------------------------------- */

%include <std_common.i>

%fragment("PySwigIterator","header") {  
namespace swig {
  struct stop_iteration {
  };

  struct PySwigIterator {
  private:
    PyObject_ptr _seq;

  protected:
    PySwigIterator(PyObject *seq) : _seq(seq)
    {
    }
      
  public:
    virtual ~PySwigIterator() {}

    // Access iterator method, required by Python
    virtual PyObject *value() const = 0;

    // Forward iterator method, required by Python
    virtual PySwigIterator *incr(size_t n = 1) = 0;
    
    // Backward iterator method, very common in C++, but not required in Python
    virtual PySwigIterator *decr(size_t /*n*/ = 1)
    {
      throw stop_iteration();
    }

    // Random access iterator methods, but not required in Python
    virtual ptrdiff_t distance(const PySwigIterator &/*x*/) const
    {
      throw std::invalid_argument("operation not supported");
    }

    virtual bool equal (const PySwigIterator &/*x*/) const
    {
      throw std::invalid_argument("operation not supported");
    }
    
    // C++ common/needed methods
    virtual PySwigIterator *copy() const = 0;

    PyObject *next()     
    {
      SWIG_PYTHON_THREAD_BEGIN_BLOCK; // disable threads       
      PyObject *obj = value();
      incr();       
      SWIG_PYTHON_THREAD_END_BLOCK; // re-enable threads
      return obj;     
    }

    PyObject *previous()
    {
      SWIG_PYTHON_THREAD_BEGIN_BLOCK; // disable threads       
      decr();
      PyObject *obj = value();
      SWIG_PYTHON_THREAD_END_BLOCK; // re-enable threads       
      return obj;
    }

    PySwigIterator *advance(ptrdiff_t n)
    {
      return  (n > 0) ?  incr(n) : decr(-n);
    }
      
    bool operator == (const PySwigIterator& x)  const
    {
      return equal(x);
    }
      
    bool operator != (const PySwigIterator& x) const
    {
      return ! operator==(x);
    }
      
    PySwigIterator& operator += (ptrdiff_t n)
    {
      return *advance(n);
    }

    PySwigIterator& operator -= (ptrdiff_t n)
    {
      return *advance(-n);
    }
      
    PySwigIterator* operator + (ptrdiff_t n) const
    {
      return copy()->advance(n);
    }

    PySwigIterator* operator - (ptrdiff_t n) const
    {
      return copy()->advance(-n);
    }
      
    ptrdiff_t operator - (const PySwigIterator& x) const
    {
      return x.distance(*this);
    }
      
    static swig_type_info* descriptor() {
      static int init = 0;
      static swig_type_info* desc = 0;
      if (!init) {
	desc = SWIG_TypeQuery("swig::PySwigIterator *");
	init = 1;
      }	
      return desc;
    }    
  };
}
}

%fragment("PySwigIterator_T","header",fragment="PySwigIterator",fragment="StdTraits",fragment="StdIteratorTraits") {
namespace swig {
  template<typename OutIterator>
  class PySwigIterator_T :  public PySwigIterator
  {
  public:
    typedef OutIterator out_iterator;
    typedef typename std::iterator_traits<out_iterator>::value_type value_type;    
    typedef PySwigIterator_T<out_iterator> self_type;

    PySwigIterator_T(out_iterator curr, PyObject *seq)
      : PySwigIterator(seq), current(curr)
    {
    }

    const out_iterator& get_current() const
    {
      return current;
    }

    
    bool equal (const PySwigIterator &iter) const
    {
      const self_type *iters = dynamic_cast<const self_type *>(&iter);
      if (iters) {
	return (current == iters->get_current());
      } else {
	throw std::invalid_argument("bad iterator type");
      }
    }
    
    ptrdiff_t distance(const PySwigIterator &iter) const
    {
      const self_type *iters = dynamic_cast<const self_type *>(&iter);
      if (iters) {
	return std::distance(current, iters->get_current());
      } else {
	throw std::invalid_argument("bad iterator type");
      }
    }    
    
  protected:
    out_iterator current;
  };
  
  template <class ValueType>
  struct from_oper 
  {
    typedef const ValueType& argument_type;
    typedef PyObject *result_type;
    result_type operator()(argument_type v) const
    {
      return swig::from(v);
    }
  };

  template<typename OutIterator, 
	   typename ValueType = typename std::iterator_traits<OutIterator>::value_type,
	   typename FromOper = from_oper<ValueType> >
  class PySwigIteratorOpen_T :  public PySwigIterator_T<OutIterator>
  {
  public:
    FromOper from;
    typedef OutIterator out_iterator;
    typedef ValueType value_type;
    typedef PySwigIterator_T<out_iterator>  base;
    typedef PySwigIteratorOpen_T<OutIterator, ValueType, FromOper> self_type;
    
    PySwigIteratorOpen_T(out_iterator curr, PyObject *seq)
      : PySwigIterator_T<OutIterator>(curr, seq)
    {
    }
    
    PyObject *value() const {
      return from(static_cast<const value_type&>(*(base::current)));
    }
    
    PySwigIterator *copy() const
    {
      return new self_type(*this);
    }

    PySwigIterator *incr(size_t n = 1)
    {
      while (n--) {
	++base::current;
      }
      return this;
    }

    PySwigIterator *decr(size_t n = 1)
    {
      while (n--) {
	--base::current;
      }
      return this;
    }
  };

  template<typename OutIterator, 
	   typename ValueType = typename std::iterator_traits<OutIterator>::value_type,
	   typename FromOper = from_oper<ValueType> >
  class PySwigIteratorClosed_T :  public PySwigIterator_T<OutIterator>
  {
  public:
    FromOper from;
    typedef OutIterator out_iterator;
    typedef ValueType value_type;
    typedef PySwigIterator_T<out_iterator>  base;    
    typedef PySwigIteratorClosed_T<OutIterator, ValueType, FromOper> self_type;
    
    PySwigIteratorClosed_T(out_iterator curr, out_iterator first, out_iterator last, PyObject *seq)
      : PySwigIterator_T<OutIterator>(curr, seq), begin(first), end(last)
    {
    }
    
    PyObject *value() const {
      if (base::current == end) {
	throw stop_iteration();
      } else {
	return from(static_cast<const value_type&>(*(base::current)));
      }
    }
    
    PySwigIterator *copy() const
    {
      return new self_type(*this);
    }

    PySwigIterator *incr(size_t n = 1)
    {
      while (n--) {
	if (base::current == end) {
	  throw stop_iteration();
	} else {
	  ++base::current;
	}
      }
      return this;
    }

    PySwigIterator *decr(size_t n = 1)
    {
      while (n--) {
	if (base::current == begin) {
	  throw stop_iteration();
	} else {
	  --base::current;
	}
      }
      return this;
    }

  private:
    out_iterator begin;
    out_iterator end;
  };

  template<typename OutIter>
  inline PySwigIterator*
  make_output_iterator(const OutIter& current, const OutIter& begin,const OutIter& end, PyObject *seq = 0)
  {
    return new PySwigIteratorClosed_T<OutIter>(current, begin, end, seq);
  }

  template<typename OutIter>
  inline PySwigIterator*
  make_output_iterator(const OutIter& current, PyObject *seq = 0)
  {
    return new PySwigIteratorOpen_T<OutIter>(current, seq);
  }
}
}


%fragment("PySwigIterator");
namespace swig 
{
  /*
    Throw a StopIteration exception
  */
  %ignore stop_iteration;
  struct stop_iteration {};
  
  %typemap(throws) stop_iteration {
    (void)$1;
    SWIG_SetErrorObj(PyExc_StopIteration, SWIG_Py_Void());
    SWIG_fail;
  }

  /* 
     Mark methods that return new objects
  */
  %newobject PySwigIterator::copy;
  %newobject PySwigIterator::operator + (ptrdiff_t n) const;
  %newobject PySwigIterator::operator - (ptrdiff_t n) const;

  %nodirector PySwigIterator;
  %extend PySwigIterator {
  %pythoncode {def __iter__(self): return self}
  }

  %catches(swig::stop_iteration) PySwigIterator::value() const;
  %catches(swig::stop_iteration) PySwigIterator::incr(size_t n = 1);
  %catches(swig::stop_iteration) PySwigIterator::decr(size_t n = 1);
  %catches(std::invalid_argument) PySwigIterator::distance(const PySwigIterator &x) const;
  %catches(std::invalid_argument) PySwigIterator::equal (const PySwigIterator &x) const;
  %catches(swig::stop_iteration) PySwigIterator::next();
  %catches(swig::stop_iteration) PySwigIterator::previous();
  %catches(swig::stop_iteration) PySwigIterator::advance(ptrdiff_t n);
  %catches(swig::stop_iteration) PySwigIterator::operator += (ptrdiff_t n);
  %catches(swig::stop_iteration) PySwigIterator::operator -= (ptrdiff_t n);
  %catches(swig::stop_iteration) PySwigIterator::operator + (ptrdiff_t n) const;
  %catches(swig::stop_iteration) PySwigIterator::operator - (ptrdiff_t n) const;


  struct PySwigIterator
  {
  protected:
    PySwigIterator(PyObject *seq);

  public:
    virtual ~PySwigIterator();

    // Access iterator method, required by Python
    virtual PyObject *value() const = 0;

    // Forward iterator method, required by Python
    virtual PySwigIterator *incr(size_t n = 1) = 0;
    
    // Backward iterator method, very common in C++, but not required in Python
    virtual PySwigIterator *decr(size_t n = 1);

    // Random access iterator methods, but not required in Python
    virtual ptrdiff_t distance(const PySwigIterator &x) const;

    virtual bool equal (const PySwigIterator &x) const;
    
    // C++ common/needed methods
    virtual PySwigIterator *copy() const = 0;

    PyObject *next();
    PyObject *previous();
    PySwigIterator *advance(ptrdiff_t n);

    bool operator == (const PySwigIterator& x)  const;
    bool operator != (const PySwigIterator& x) const;
    PySwigIterator& operator += (ptrdiff_t n);
    PySwigIterator& operator -= (ptrdiff_t n);
    PySwigIterator* operator + (ptrdiff_t n) const;
    PySwigIterator* operator - (ptrdiff_t n) const;
    ptrdiff_t operator - (const PySwigIterator& x) const;
  };
}

