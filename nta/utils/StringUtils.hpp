/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

/** @file 
 * Utility functions for string conversion
 */

#ifndef NTA_STRING_UTILS_HPP
#define NTA_STRING_UTILS_HPP


#include <nta/types/types.hpp>
#include <boost/shared_array.hpp>
#include <string>
#include <vector>
#include <set>
#include <cmath>

namespace nta 
{
  // TODO: Should this be a namespace instead of a class?
  class StringUtils
  {
  public:
    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Convert string to a typed value (using stringstream)
     * Bool: Convert a string to a bool. Accepts "true", "yes", "1", with different
     *       capitalizations. Anything else returns false. 
     * Int32/Int64/etc Convert a string to a numerical type. 
     * Uses a stringstream to convert.
     *
     * @param s            a string to convert
     * @param throwOnError a bool that determines if to throw an error on failure
     * @param fail         a bool pointer that if not NULL gets set to true if the conversion fails
     * @retval    boolean value
     */
    static bool toBool(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static UInt32 toUInt32(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static Int32 toInt32(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static UInt64 toUInt64(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static Real32 toReal32(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static Real64 toReal64(const std::string& s, bool throwOnError = false, bool * fail = NULL);
    static size_t toSizeT(const std::string& s, bool throwOnError = false, bool * fail = NULL);

    static bool startsWith(const std::string& s, const std::string& prefix);
    static bool endsWith(const std::string& s, const std::string& ending);
    



    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Convert an integer to a string 
     *
     * @param i   an integer to convert
     * @retval    string
     */

    static std::string fromInt(long long i);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Base64 encode a string 
     *
     * @param s   a string to encode
     * @retval    encoded string
     */

    static std::string base64Encode(const std::string& s);


    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Base64 encode a memory buffer
     *
     * @param buf   buffer containing the data to encode
     * @param inLen the length in bytes of the buffer to encode
     * @retval      encoded string
     */
    static std::string base64Encode(const void* buf, Size inLen);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Base64 decode a string 
     *
     * @param s   a string to decode
     * @retval    decoded string
     */

    static std::string base64Decode(const std::string& s);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Base64 decode from a memory buffer
     *
     * @param buf a buffer to decode
     * @param inLen length of buffer
     * @retval    decoded string
     */
    static std::string base64Decode(const void* buf, Size inLen);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Represent a binary buffer with a hexidecimal string
     *
     * @param buf a buffer to represent
     * @param inLen length of buffer
     * @retval    hexidecimal string
     */
    static std::string hexEncode(const void* buf, Size inLen);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Convert a string specifying a list of unsigned numbers into a vector.
     * The string can be of the form "0-9,10, 12, 13-19". 
     *
     * If 'allowAll' is true, the empty string and the string "all" both return an empty list. 
     * If 'allowAll' is not true, only integer lists are accepted and the empty string and 
     *  the string "all" throw an exception 
     *
     * @param s        a string to convert
     * @param list     vector to fill in
     * @param allowAll if true, s can be set to "all"
     * @param asRanges if true, list is filled in as pairs of integers that specify the begin
     *                  and size of each range of integers in s. If false, list contains 
     *                  each and every one of the integers specified by s. 
     * @retval     void
     */
    static void toIntList(const std::string& s, std::vector<Int>& list, bool allowAll=false,
                          bool asRanges=false);

    /**
     * Non-throwing version of toIntList.
     *
     * If 'allowAll' is true, the empty string and the string "all" both return an empty list. 
     * If 'allowAll' is not true, only integer lists are accepted and the empty string and 
     *  the string "all" throw an exception 
     *
     * @param s   a string to convert
     * @param v   vector to fill in
     * @retval    true if successfully parsed. false if a parsing error occurred
     */
    static bool toIntListNoThrow(const std::string& s, std::vector<Int>& list, 
      bool allowAll=false, bool asRanges=false);

    //--------------------------------------------------------------------------------
    /**
     * @b Responsibility:
     * Convert a string specifying a list of unsigned numbers into pointer to an array of
     * bytes that specify a mask of which numbers were included in the list. If a number
     * is in the list, the corresponding bit will be set in the mask. Each byte specifies
     * 8 bits of the mask, bit 0 of byte 0 holds entry 0, bit 1 of byte 0 holds entry 1, etc.
     *
     * The string can be of the form "0-9,10, 12, 13-19", "all", or "". Both "all" and ""
     * are special cases representing all bits and return a boost::shared_array with a
     * NIL pointer (retval.get() == NULL). 
     *
     * @param s         a string to convert
     * @param bitCount  number of bits to include in the return mask. 
     * @retval          boost::shared_array containing the dynamically allocated mask
     *
     */
    static boost::shared_array<Byte> toByteArray(const std::string& s, Size bitCount);

  };
}

#endif // NTA_STRING_UTILS_HPP
