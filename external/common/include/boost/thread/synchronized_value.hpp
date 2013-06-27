// (C) Copyright 2010 Just Software Solutions Ltd http://www.justsoftwaresolutions.co.uk
// (C) Copyright 2012 Vicente J. Botet Escriba
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)


#ifndef BOOST_THREAD_SYNCHRONIZED_VALUE_HPP
#define BOOST_THREAD_SYNCHRONIZED_VALUE_HPP

#include <boost/thread/detail/config.hpp>

#include <boost/thread/detail/move.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/lock_types.hpp>
#include <boost/thread/lock_guard.hpp>
#include <boost/thread/lock_algorithms.hpp>
#include <boost/thread/lock_factories.hpp>
#include <boost/thread/strict_lock.hpp>
#include <boost/utility/swap.hpp>

#include <boost/config/abi_prefix.hpp>

namespace boost
{

  /**
   *
   */
  template <typename T, typename Lockable = mutex>
  class const_strict_lock_ptr
  {
  public:
    typedef T value_type;
    typedef Lockable lockable_type;
  protected:

    // this should be a strict_lock, but we need to be able to return it.
    boost::unique_lock<lockable_type> lk_;
    T const& value_;

  public:
    BOOST_THREAD_MOVABLE_ONLY( const_strict_lock_ptr )

    const_strict_lock_ptr(T const& value, Lockable & mtx) :
      lk_(mtx), value_(value)
    {
    }

    const_strict_lock_ptr(BOOST_THREAD_RV_REF(const_strict_lock_ptr) other)
    : lk_(boost::move(BOOST_THREAD_RV(other).lk_)),value_(BOOST_THREAD_RV(other).value_)
    {
    }

    ~const_strict_lock_ptr()
    {
    }

    const T* operator->() const
    {
      return &value_;
    }

    const T& operator*() const
    {
      return value_;
    }

  };

  /**
   *
   */
  template <typename T, typename Lockable = mutex>
  class strict_lock_ptr : public const_strict_lock_ptr<T,Lockable>
  {
    typedef const_strict_lock_ptr<T,Lockable> base_type;
  public:
    BOOST_THREAD_MOVABLE_ONLY( strict_lock_ptr )

    strict_lock_ptr(T & value, Lockable & mtx) :
    base_type(value, mtx)
    {
    }

    strict_lock_ptr(BOOST_THREAD_RV_REF(strict_lock_ptr) other)
    : base_type(boost::move(static_cast<base_type&>(other)))
    {
    }

    ~strict_lock_ptr()
    {
    }

    T* operator->()
    {
      return const_cast<T*>(&this->value_);
    }

    T& operator*()
    {
      return const_cast<T&>(this->value_);
    }

  };

  /**
   *
   */
  template <typename T, typename Lockable = mutex>
  class const_unique_lock_ptr : public unique_lock<Lockable>
  {
    typedef unique_lock<Lockable> base_type;
  public:
    typedef T value_type;
    typedef Lockable lockable_type;
  protected:
    T const& value_;

  public:
    BOOST_THREAD_MOVABLE_ONLY(const_unique_lock_ptr)

    const_unique_lock_ptr(T const& value, Lockable & mtx)
    : base_type(mtx), value_(value)
    {
    }
    const_unique_lock_ptr(T const& value, Lockable & mtx, adopt_lock_t)
    : base_type(mtx, adopt_lock), value_(value)
    {
    }
    const_unique_lock_ptr(T const& value, Lockable & mtx, defer_lock_t)
    : base_type(mtx, defer_lock), value_(value)
    {
    }
    const_unique_lock_ptr(T const& value, Lockable & mtx, try_to_lock_t)
    : base_type(mtx, try_to_lock), value_(value)
    {
    }
    const_unique_lock_ptr(BOOST_THREAD_RV_REF(const_unique_lock_ptr) other)
    : base_type(boost::move(static_cast<base_type&>(other))), value_(BOOST_THREAD_RV(other).value_)
    {
    }

    ~const_unique_lock_ptr()
    {
    }

    const T* operator->() const
    {
      BOOST_ASSERT (this->owns_lock());
      return &value_;
    }

    const T& operator*() const
    {
      BOOST_ASSERT (this->owns_lock());
      return value_;
    }

  };

  /**
   *
   */
  template <typename T, typename Lockable = mutex>
  class unique_lock_ptr : public const_unique_lock_ptr<T, Lockable>
  {
    typedef const_unique_lock_ptr<T, Lockable> base_type;
  public:
    typedef T value_type;
    typedef Lockable lockable_type;

    BOOST_THREAD_MOVABLE_ONLY(unique_lock_ptr)

    unique_lock_ptr(T & value, Lockable & mtx)
    : base_type(value, mtx)
    {
    }
    unique_lock_ptr(T & value, Lockable & mtx, adopt_lock_t)
    : base_type(value, mtx, adopt_lock)
    {
    }
    unique_lock_ptr(T & value, Lockable & mtx, defer_lock_t)
    : base_type(value, mtx, defer_lock)
    {
    }
    unique_lock_ptr(T & value, Lockable & mtx, try_to_lock_t)
    : base_type(value, mtx, try_to_lock)
    {
    }
    unique_lock_ptr(BOOST_THREAD_RV_REF(unique_lock_ptr) other)
    : base_type(boost::move(static_cast<base_type&>(other)))
    {
    }

    ~unique_lock_ptr()
    {
    }

    T* operator->()
    {
      BOOST_ASSERT (this->owns_lock());
      return const_cast<T*>(&this->value_);
    }

    T& operator*()
    {
      BOOST_ASSERT (this->owns_lock());
      return const_cast<T&>(this->value_);
    }


  };

  /**
   *
   */
  template <typename T, typename Lockable = mutex>
  class synchronized_value
  {
  public:
    typedef T value_type;
    typedef Lockable lockable_type;
  private:
    T value_;
    mutable lockable_type mtx_;
  public:
    /**
     * Default constructor.
     *
     * Requires: T is DefaultConstructible
     */
    synchronized_value()
    : value_()
    {
    }

    /**
     * Constructor from copy constructible value.
     *
     * Requires: T is CopyConstructible
     */
    synchronized_value(T const& other)
    : value_(other)
    {
    }

    /**
     * Move Constructor from movable value.
     *
     * Requires: T is Movable
     */
    synchronized_value(BOOST_THREAD_RV_REF(T) other)
    : value_(boost::move(other))
    {
    }

    /**
     * Copy Constructor.
     *
     * Requires: T is DefaultConstructible and Assignable
     * Effects: Assigns the value on a scope protected by the mutex of the rhs. The mutex is not copied.
     */
    synchronized_value(synchronized_value const& rhs)
    {
      strict_lock<lockable_type> lk(rhs.mtx_);
      value_ = rhs.value_;
    }

    /**
     * Move Constructor.
     *
     */
    synchronized_value(BOOST_THREAD_RV_REF(synchronized_value) other)
    {
      strict_lock<lockable_type> lk(other.mtx_);
      value_= boost::move(other);
    }

    /**
     * Assignment operator.
     *
     * Effects: Copies the underlying value on a scope protected by the two mutexes.
     * The mutexes are not copied. The locks are acquired using lock, so deadlock is avoided.
     * For example, there is no problem if one thread assigns a = b and the other assigns b = a.
     *
     * Return: *this
     */

    synchronized_value& operator=(synchronized_value const& rhs)
    {
      if(&rhs != this)
      {
        // auto _ = make_unique_locks(mtx_, rhs.mtx_);
        unique_lock<lockable_type> lk1(mtx_, defer_lock);
        unique_lock<lockable_type> lk2(rhs.mtx_, defer_lock);
        lock(lk1,lk2);

        value_ = rhs.value_;
      }
      return *this;
    }
    /**
     * Assignment operator from a T const&.
     * Effects: The operator copies the value on a scope protected by the mutex.
     * Return: *this
     */
    synchronized_value& operator=(value_type const& value)
    {
      {
        strict_lock<lockable_type> lk(mtx_);
        value_ = value;
      }
      return *this;
    }

    /**
     * Explicit conversion to value type.
     *
     * Requires: T is CopyConstructible
     * Return: A copy of the protected value obtained on a scope protected by the mutex.
     *
     */
    T get() const
    {
      strict_lock<lockable_type> lk(mtx_);
      return value_;
    }
    /**
     * Explicit conversion to value type.
     *
     * Requires: T is CopyConstructible
     * Return: A copy of the protected value obtained on a scope protected by the mutex.
     *
     */
#if ! defined(BOOST_NO_CXX11_EXPLICIT_CONVERSION_OPERATORS)
    explicit operator T() const
    {
      return get();
    }
#endif

    /**
     * Swap
     *
     * Effects: Swaps the data. Again, locks are acquired using lock(). The mutexes are not swapped.
     * A swap method accepts a T& and swaps the data inside a critical section.
     * This is by far the preferred method of changing the guarded datum wholesale because it keeps the lock only
     * for a short time, thus lowering the pressure on the mutex.
     */
    void swap(synchronized_value & rhs)
    {
      if (this == &rhs) {
        return;
      }
      // auto _ = make_unique_locks(mtx_, rhs.mtx_);
      unique_lock<lockable_type> lk1(mtx_, defer_lock);
      unique_lock<lockable_type> lk2(rhs.mtx_, defer_lock);
      lock(lk1,lk2);
      boost::swap(value_, rhs.value_);
    }
    /**
     * Swap with the underlying type
     *
     * Effects: Swaps the data on a scope protected by the mutex.
     */
    void swap(value_type & rhs)
    {
      strict_lock<lockable_type> lk(mtx_);
      boost::swap(value_, rhs.value_);
    }



    /**
     * Essentially calling a method obj->foo(x, y, z) calls the method foo(x, y, z) inside a critical section as
     * long-lived as the call itself.
     */
    strict_lock_ptr<T,Lockable> operator->()
    {
      return BOOST_THREAD_MAKE_RV_REF((strict_lock_ptr<T,Lockable>(value_, mtx_)));
    }
    /**
     * If the synchronized_value object involved is const-qualified, then you'll only be able to call const methods
     * through operator->. So, for example, vec->push_back("xyz") won't work if vec were const-qualified.
     * The locking mechanism capitalizes on the assumption that const methods don't modify their underlying data.
     */
    const_strict_lock_ptr<T,Lockable> operator->() const
    {
      return BOOST_THREAD_MAKE_RV_REF((const_strict_lock_ptr<T,Lockable>(value_, mtx_)));
    }

    /**
     * The synchronize() factory make easier to lock on a scope.
     * As discussed, operator-> can only lock over the duration of a call, so it is insufficient for complex operations.
     * With synchronize() you get to lock the object in a scoped and to directly access the object inside that scope.
     *
     * Example
     *   void fun(synchronized_value<vector<int>> & vec) {
     *     auto&& vec=vec.synchronize();
     *     vec.push_back(42);
     *     assert(vec.back() == 42);
     *   }
     */
    strict_lock_ptr<T,Lockable> synchronize()
    {
      return BOOST_THREAD_MAKE_RV_REF((strict_lock_ptr<T,Lockable>(value_, mtx_)));
    }
    const_strict_lock_ptr<T,Lockable> synchronize() const
    {
      return BOOST_THREAD_MAKE_RV_REF((const_strict_lock_ptr<T,Lockable>(value_, mtx_)));
    }

    unique_lock_ptr<T,Lockable> unique_synchronize()
    {
      return BOOST_THREAD_MAKE_RV_REF((unique_lock_ptr<T,Lockable>(value_, mtx_)));
    }
    unique_lock_ptr<T,Lockable> unique_synchronize(defer_lock_t tag)
    {
      return BOOST_THREAD_MAKE_RV_REF((unique_lock_ptr<T,Lockable>(value_, mtx_, tag)));
    }
    const_unique_lock_ptr<T,Lockable> unique_synchronize() const
    {
      return BOOST_THREAD_MAKE_RV_REF((const_unique_lock_ptr<T,Lockable>(value_, mtx_)));
    }
    const_unique_lock_ptr<T,Lockable> unique_synchronize(defer_lock_t tag) const
    {
      return BOOST_THREAD_MAKE_RV_REF((const_unique_lock_ptr<T,Lockable>(value_, mtx_, tag)));
    }


  private:
    class deref_value
    {
    private:
      friend class synchronized_value;

      boost::unique_lock<lockable_type> lk_;
      T& value_;

      explicit deref_value(synchronized_value& outer):
      lk_(outer.mtx_),value_(outer.value_)
      {}

    public:
      BOOST_THREAD_MOVABLE_ONLY(deref_value)

      deref_value(BOOST_THREAD_RV_REF(deref_value) other):
      lk_(boost::move(BOOST_THREAD_RV(other).lk_)),value_(BOOST_THREAD_RV(other).value_)
      {}
      operator T()
      {
        return value_;
      }

      deref_value& operator=(T const& newVal)
      {
        value_=newVal;
        return *this;
      }
    };
    class const_deref_value
    {
    private:
      friend class synchronized_value;

      boost::unique_lock<lockable_type> lk_;
      const T& value_;

      explicit const_deref_value(synchronized_value const& outer):
      lk_(outer.mtx_), value_(outer.value_)
      {}

    public:
      BOOST_THREAD_MOVABLE_ONLY(const_deref_value)

      const_deref_value(BOOST_THREAD_RV_REF(const_deref_value) other):
      lk_(boost::move(BOOST_THREAD_RV(other).lk_)), value_(BOOST_THREAD_RV(other).value_)
      {}

      operator T()
      {
        return value_;
      }
    };

  public:
    deref_value operator*()
    {
      return BOOST_THREAD_MAKE_RV_REF(deref_value(*this));
    }

    const_deref_value operator*() const
    {
      return BOOST_THREAD_MAKE_RV_REF(const_deref_value(*this));
    }

  };

  /**
   *
   */
  template <typename T, typename L>
  inline void swap(synchronized_value<T,L> & lhs, synchronized_value<T,L> & rhs)
  {
    lhs.swap(rhs);
  }

}

#include <boost/config/abi_suffix.hpp>

#endif // header
