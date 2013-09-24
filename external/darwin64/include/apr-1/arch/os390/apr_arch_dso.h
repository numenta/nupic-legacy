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

#ifndef DSO_H
#define DSO_H

#include "apr_private.h"
#include "apr_general.h"
#include "apr_pools.h"
#include "apr_dso.h"
#include "apr.h"

#if APR_HAS_DSO

#include <dll.h>

struct apr_dso_handle_t {
    dllhandle  *handle;     /* Handle to the DSO loaded            */
    int failing_errno;      /* Don't save the buffer returned by
                               strerror(); it gets reused          */
    apr_pool_t *pool;
};

#endif

#endif
