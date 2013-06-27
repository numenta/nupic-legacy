///////////////////////////////////////////////////////////////
//  Copyright 2011 John Maddock. Distributed under the Boost
//  Software License, Version 1.0. (See accompanying file
//  LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_

#ifndef BOOST_MATH_RATIONAL_ADAPTER_HPP
#define BOOST_MATH_RATIONAL_ADAPTER_HPP

#include <iostream>
#include <iomanip>
#include <sstream>
#include <boost/cstdint.hpp>
#include <boost/multiprecision/number.hpp>
#ifdef BOOST_MSVC
#  pragma warning(push)
#  pragma warning(disable:4512 4127)
#endif
#include <boost/rational.hpp>
#ifdef BOOST_MSVC
#  pragma warning(pop)
#endif

namespace boost{
namespace multiprecision{
namespace backends{

template <class IntBackend>
struct rational_adapter
{
   typedef number<IntBackend>                integer_type;
   typedef boost::rational<integer_type>        rational_type;

   typedef typename IntBackend::signed_types    signed_types;
   typedef typename IntBackend::unsigned_types  unsigned_types;
   typedef typename IntBackend::float_types     float_types;

   rational_adapter(){}
   rational_adapter(const rational_adapter& o)
   {
      m_value = o.m_value;
   }
   rational_adapter(const IntBackend& o) : m_value(o) {}

   template <class U>
   rational_adapter(const U& u, typename enable_if_c<is_convertible<U, IntBackend>::value>::type* = 0) 
      : m_value(IntBackend(u)){}
   template <class U>
   explicit rational_adapter(const U& u, 
      typename enable_if_c<
         boost::multiprecision::detail::is_explicitly_convertible<U, IntBackend>::value && !is_convertible<U, IntBackend>::value
      >::type* = 0) 
      : m_value(IntBackend(u)){}
   template <class U>
   typename enable_if_c<(boost::multiprecision::detail::is_explicitly_convertible<U, IntBackend>::value && !is_arithmetic<U>::value), rational_adapter&>::type operator = (const U& u) 
   {
      m_value = IntBackend(u);
   }

#ifndef BOOST_NO_CXX11_RVALUE_REFERENCES
   rational_adapter(rational_adapter&& o) : m_value(o.m_value) {}
   rational_adapter(IntBackend&& o) : m_value(o) {}
   rational_adapter& operator = (rational_adapter&& o)
   {
      m_value = static_cast<rational_type&&>(o.m_value);
      return *this;
   }
#endif
   rational_adapter& operator = (const rational_adapter& o)
   {
      m_value = o.m_value;
      return *this;
   }
   rational_adapter& operator = (const IntBackend& o)
   {
      m_value = o;
      return *this;
   }
   template <class Int>
   typename enable_if<is_integral<Int>, rational_adapter&>::type operator = (Int i)
   {
      m_value = i;
      return *this;
   }
   template <class Float>
   typename enable_if<is_floating_point<Float>, rational_adapter&>::type operator = (Float i)
   {
      int e;
      Float f = std::frexp(i, &e);
      f = std::ldexp(f, std::numeric_limits<Float>::digits);
      e -= std::numeric_limits<Float>::digits;
      integer_type num(f);
      integer_type denom(1u);
      if(e > 0)
      {
         num <<= e;
      }
      else if(e < 0)
      {
         denom <<= -e;
      }
      m_value.assign(num, denom);
      return *this;
   }
   rational_adapter& operator = (const char* s)
   {
      std::string s1;
      multiprecision::number<IntBackend> v1, v2;
      char c;
      bool have_hex = false;
      const char* p = s; // saved for later

      while((0 != (c = *s)) && (c == 'x' || c == 'X' || c == '-' || c == '+' || (c >= '0' && c <= '9') || (have_hex && (c >= 'a' && c <= 'f')) || (have_hex && (c >= 'A' && c <= 'F'))))
      {
         if(c == 'x' || c == 'X')
            have_hex = true;
         s1.append(1, c);
         ++s;
      }
      v1.assign(s1);
      s1.erase();
      if(c == '/')
      {
         ++s;
         while((0 != (c = *s)) && (c == 'x' || c == 'X' || c == '-' || c == '+' || (c >= '0' && c <= '9') || (have_hex && (c >= 'a' && c <= 'f')) || (have_hex && (c >= 'A' && c <= 'F'))))
         {
            if(c == 'x' || c == 'X')
               have_hex = true;
            s1.append(1, c);
            ++s;
         }
         v2.assign(s1);
      }
      else
         v2 = 1;
      if(*s)
      {
         BOOST_THROW_EXCEPTION(std::runtime_error(std::string("Could parse the string \"") + p + std::string("\" as a valid rational number.")));
      }
      data().assign(v1, v2);
      return *this;
   }
   void swap(rational_adapter& o)
   {
      std::swap(m_value, o.m_value);
   }
   std::string str(std::streamsize digits, std::ios_base::fmtflags f)const
   {
      //
      // We format the string ourselves so we can match what GMP's mpq type does:
      //
      std::string result = data().numerator().str(digits, f);
      if(data().denominator() != 1)
      {
         result.append(1, '/');
         result.append(data().denominator().str(digits, f));
      }
      return result;
   }
   void negate()
   {
      m_value = -m_value;
   }
   int compare(const rational_adapter& o)const
   {
      return m_value > o.m_value ? 1 : (m_value < o.m_value ? -1 : 0);
   }
   template <class Arithmatic>
   typename enable_if<is_arithmetic<Arithmatic>, int>::type compare(Arithmatic i)const
   {
      return m_value > i ? 1 : (m_value < i ? -1 : 0);
   }
   rational_type& data() { return m_value; }
   const rational_type& data()const { return m_value; }
private:
   rational_type m_value;
};

template <class IntBackend>
inline void eval_add(rational_adapter<IntBackend>& result, const rational_adapter<IntBackend>& o)
{
   result.data() += o.data();
}
template <class IntBackend>
inline void eval_subtract(rational_adapter<IntBackend>& result, const rational_adapter<IntBackend>& o)
{
   result.data() -= o.data();
}
template <class IntBackend>
inline void eval_multiply(rational_adapter<IntBackend>& result, const rational_adapter<IntBackend>& o)
{
   result.data() *= o.data();
}
template <class IntBackend>
inline void eval_divide(rational_adapter<IntBackend>& result, const rational_adapter<IntBackend>& o)
{
   using default_ops::eval_is_zero;
   if(eval_is_zero(o))
   {
      BOOST_THROW_EXCEPTION(std::overflow_error("Divide by zero."));
   }
   result.data() /= o.data();
}

template <class R, class IntBackend>
inline void eval_convert_to(R* result, const rational_adapter<IntBackend>& backend)
{
   *result = backend.data().numerator().template convert_to<R>();
   *result /= backend.data().denominator().template convert_to<R>();
}

template <class IntBackend>
inline bool eval_is_zero(const rational_adapter<IntBackend>& val)
{
   return eval_is_zero(val.data().numerator().backend());
}
template <class IntBackend>
inline int eval_get_sign(const rational_adapter<IntBackend>& val)
{
   return eval_get_sign(val.data().numerator().backend());
}

template<class IntBackend, class V>
inline void assign_components(rational_adapter<IntBackend>& result, const V& v1, const V& v2)
{
   result.data().assign(v1, v2);
}

} // namespace backends

template<class IntBackend>
struct expression_template_default<backends::rational_adapter<IntBackend> > : public expression_template_default<IntBackend> {};
   
template<class IntBackend>
struct number_category<backends::rational_adapter<IntBackend> > : public mpl::int_<number_kind_rational>{};

using boost::multiprecision::backends::rational_adapter;

template <class T>
struct component_type<rational_adapter<T> >
{
   typedef number<T> type;
};

template <class IntBackend, expression_template_option ET>
inline number<IntBackend, ET> numerator(const number<rational_adapter<IntBackend>, ET>& val)
{
   return val.backend().data().numerator();
}
template <class IntBackend, expression_template_option ET>
inline number<IntBackend, ET> denominator(const number<rational_adapter<IntBackend>, ET>& val)
{
   return val.backend().data().denominator();
}

#ifdef BOOST_NO_SFINAE_EXPR

namespace detail{

template<class U, class IntBackend>
struct is_explicitly_convertible<U, rational_adapter<IntBackend> > : public is_explicitly_convertible<U, IntBackend> {};

}

#endif

}} // namespaces


namespace std{

template <class IntBackend, boost::multiprecision::expression_template_option ExpressionTemplates>
class numeric_limits<boost::multiprecision::number<boost::multiprecision::rational_adapter<IntBackend>, ExpressionTemplates> > : public std::numeric_limits<boost::multiprecision::number<IntBackend, ExpressionTemplates> >
{
   typedef std::numeric_limits<boost::multiprecision::number<IntBackend> > base_type;
   typedef boost::multiprecision::number<boost::multiprecision::rational_adapter<IntBackend> > number_type;
public:
   BOOST_STATIC_CONSTEXPR bool is_integer = false;
   BOOST_STATIC_CONSTEXPR bool is_exact = true;
   BOOST_STATIC_CONSTEXPR number_type (min)() { return (base_type::min)(); }
   BOOST_STATIC_CONSTEXPR number_type (max)() { return (base_type::max)(); }
   BOOST_STATIC_CONSTEXPR number_type lowest() { return -(max)(); }
   BOOST_STATIC_CONSTEXPR number_type epsilon() { return base_type::epsilon(); }
   BOOST_STATIC_CONSTEXPR number_type round_error() { return epsilon() / 2; }
   BOOST_STATIC_CONSTEXPR number_type infinity() { return base_type::infinity(); }
   BOOST_STATIC_CONSTEXPR number_type quiet_NaN() { return base_type::quiet_NaN(); }
   BOOST_STATIC_CONSTEXPR number_type signaling_NaN() { return base_type::signaling_NaN(); }
   BOOST_STATIC_CONSTEXPR number_type denorm_min() { return base_type::denorm_min(); }
};

#ifndef BOOST_NO_INCLASS_MEMBER_INITIALIZATION

template <class IntBackend, boost::multiprecision::expression_template_option ExpressionTemplates>
BOOST_CONSTEXPR_OR_CONST bool numeric_limits<boost::multiprecision::number<boost::multiprecision::rational_adapter<IntBackend>, ExpressionTemplates> >::is_integer;
template <class IntBackend, boost::multiprecision::expression_template_option ExpressionTemplates>
BOOST_CONSTEXPR_OR_CONST bool numeric_limits<boost::multiprecision::number<boost::multiprecision::rational_adapter<IntBackend>, ExpressionTemplates> >::is_exact;

#endif


}

#endif
