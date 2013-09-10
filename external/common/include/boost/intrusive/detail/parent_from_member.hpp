/////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga  2007-2012
//
// Distributed under the Boost Software License, Version 1.0.
//    (See accompanying file LICENSE_1_0.txt or copy at
//          http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/intrusive for documentation.
//
/////////////////////////////////////////////////////////////////////////////
#ifndef BOOST_INTRUSIVE_DETAIL_PARENT_FROM_MEMBER_HPP
#define BOOST_INTRUSIVE_DETAIL_PARENT_FROM_MEMBER_HPP

#include <boost/intrusive/detail/config_begin.hpp>
#include <cstddef>

#if defined(BOOST_MSVC) || ((defined(_WIN32) || defined(__WIN32__) || defined(WIN32)) && defined(BOOST_INTEL))

#define BOOST_INTRUSIVE_MSVC_COMPLIANT_PTR_TO_MEMBER
#include <boost/cstdint.hpp>
#endif

namespace boost {
namespace intrusive {
namespace detail {

template<class Parent, class Member>
inline std::ptrdiff_t offset_from_pointer_to_member(const Member Parent::* ptr_to_member)
{
   //The implementation of a pointer to member is compiler dependent.
   #if defined(BOOST_INTRUSIVE_MSVC_COMPLIANT_PTR_TO_MEMBER)
   //msvc compliant compilers use their the first 32 bits as offset (even in 64 bit mode)
   union caster_union
   {
      const Member Parent::* ptr_to_member;
      boost::int32_t offset;
   } caster;
   caster.ptr_to_member = ptr_to_member;
   return std::ptrdiff_t(caster.offset);
   //This works with gcc, msvc, ac++, ibmcpp
   #elif defined(__GNUC__)   || defined(__HP_aCC) || defined(BOOST_INTEL) || \
         defined(__IBMCPP__) || defined(__DECCXX)
   const Parent * const parent = 0;
   const char *const member = static_cast<const char*>(static_cast<const void*>(&(parent->*ptr_to_member)));
   return std::ptrdiff_t(member - static_cast<const char*>(static_cast<const void*>(parent)));
   #else
   //This is the traditional C-front approach: __MWERKS__, __DMC__, __SUNPRO_CC
   union caster_union
   {
      const Member Parent::* ptr_to_member;
      std::ptrdiff_t offset;
   } caster;
   caster.ptr_to_member = ptr_to_member;
   return caster.offset - 1;
   #endif
}

template<class Parent, class Member>
inline Parent *parent_from_member(Member *member, const Member Parent::* ptr_to_member)
{
   return static_cast<Parent*>
      (
         static_cast<void*>
         (
            static_cast<char*>(static_cast<void*>(member)) - offset_from_pointer_to_member(ptr_to_member)
         )
      );
}

template<class Parent, class Member>
inline const Parent *parent_from_member(const Member *member, const Member Parent::* ptr_to_member)
{
   return static_cast<const Parent*>
      (
         static_cast<const void*>
         (
            static_cast<const char*>(static_cast<const void*>(member)) - offset_from_pointer_to_member(ptr_to_member)
         )
      );
}

}  //namespace detail {
}  //namespace intrusive {
}  //namespace boost {

#ifdef BOOST_INTRUSIVE_MSVC_COMPLIANT_PTR_TO_MEMBER
#undef BOOST_INTRUSIVE_MSVC_COMPLIANT_PTR_TO_MEMBER
#endif

#include <boost/intrusive/detail/config_end.hpp>

#endif   //#ifndef BOOST_INTRUSIVE_DETAIL_PARENT_FROM_MEMBER_HPP
