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

#ifndef _APR_SKIPLIST_P_H
#define _APR_SKIPLIST_P_H

#include "apr.h"
#include "apr_portable.h"
#include <stdlib.h>


/* This is the function type that must be implemented per object type
   that is used in a skiplist for comparisons to maintain order */
typedef int (*apr_skiplist_compare) (void *, void *);
typedef void (*apr_skiplist_freefunc) (void *);

struct apr_skiplist;
struct apr_skiplistnode;

typedef struct apr_skiplistnode apr_skiplistnode;
typedef struct apr_skiplist apr_skiplist;

APR_DECLARE(void *) apr_skiplist_alloc(apr_skiplist *sl, size_t size);

APR_DECLARE(void) apr_skiplist_free(apr_skiplist *sl, void *mem);

APR_DECLARE(apr_status_t) apr_skiplist_init(apr_skiplist **sl, apr_pool_t *p);

APR_DECLARE(void) apr_skiplist_set_compare(apr_skiplist *sl, apr_skiplist_compare,
                             apr_skiplist_compare);

APR_DECLARE(void) apr_skiplist_add_index(apr_skiplist *sl, apr_skiplist_compare,
                        apr_skiplist_compare);

APR_DECLARE(apr_skiplistnode *) apr_skiplist_getlist(apr_skiplist *sl);

APR_DECLARE(void *) apr_skiplist_find_compare(apr_skiplist *sl,
                               void *data,
                               apr_skiplistnode **iter,
                               apr_skiplist_compare func);

APR_DECLARE(void *) apr_skiplist_find(apr_skiplist *sl, void *data, apr_skiplistnode **iter);

APR_DECLARE(void *) apr_skiplist_next(apr_skiplist *sl, apr_skiplistnode **iter);

APR_DECLARE(void *) apr_skiplist_previous(apr_skiplist *sl, apr_skiplistnode **iter);


APR_DECLARE(apr_skiplistnode *) apr_skiplist_insert_compare(apr_skiplist *sl,
                                          void *data, apr_skiplist_compare comp);

APR_DECLARE(apr_skiplistnode *) apr_skiplist_insert(apr_skiplist* sl, void *data);

APR_DECLARE(int) apr_skiplist_remove_compare(apr_skiplist *sl, void *data,
                               apr_skiplist_freefunc myfree, apr_skiplist_compare comp);

APR_DECLARE(int) apr_skiplist_remove(apr_skiplist *sl, void *data, apr_skiplist_freefunc myfree);

APR_DECLARE(void) apr_skiplist_remove_all(apr_skiplist *sl, apr_skiplist_freefunc myfree);

APR_DECLARE(void) apr_skiplist_destroy(apr_skiplist *sl, apr_skiplist_freefunc myfree);

APR_DECLARE(void *) apr_skiplist_pop(apr_skiplist *a, apr_skiplist_freefunc myfree);

APR_DECLARE(void *) apr_skiplist_peek(apr_skiplist *a);

APR_DECLARE(apr_skiplist *) apr_skiplist_merge(apr_skiplist *sl1, apr_skiplist *sl2);

#endif
