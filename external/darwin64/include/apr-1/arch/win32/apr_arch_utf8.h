/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef UTF8_H
#define UTF8_H

#include "apr.h"
#include "apr_lib.h"
#include "apr_errno.h"

/* If we ever support anything more exciting than char... this could move.
 */
typedef apr_uint16_t apr_wchar_t;

/**
 * An APR internal function for fast utf-8 octet-encoded Unicode conversion
 * to the ucs-2 wide Unicode format.  This function is used for filename and 
 * other resource conversions for platforms providing native Unicode support.
 *
 * @tip Only the errors APR_EINVAL and APR_INCOMPLETE may occur, the former
 * when the character code is invalid (in or out of context) and the later
 * when more characters were expected, but insufficient characters remain.
 */
APR_DECLARE(apr_status_t) apr_conv_utf8_to_ucs2(const char *in, 
                                                apr_size_t *inbytes,
                                                apr_wchar_t *out, 
                                                apr_size_t *outwords);

/**
 * An APR internal function for fast ucs-2 wide Unicode format conversion to 
 * the utf-8 octet-encoded Unicode.  This function is used for filename and 
 * other resource conversions for platforms providing native Unicode support.
 *
 * @tip Only the errors APR_EINVAL and APR_INCOMPLETE may occur, the former
 * when the character code is invalid (in or out of context) and the later
 * when more words were expected, but insufficient words remain.
 */
APR_DECLARE(apr_status_t) apr_conv_ucs2_to_utf8(const apr_wchar_t *in, 
                                                apr_size_t *inwords,
                                                char *out, 
                                                apr_size_t *outbytes);

#endif /* def UTF8_H */
