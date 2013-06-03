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

#ifndef APR_RANDOM_H
#define APR_RANDOM_H

#include <apr_pools.h>

typedef struct apr_crypto_hash_t apr_crypto_hash_t;

typedef void apr_crypto_hash_init_t(apr_crypto_hash_t *hash);
typedef void apr_crypto_hash_add_t(apr_crypto_hash_t *hash,const void *data,
                                   apr_size_t bytes);
typedef void apr_crypto_hash_finish_t(apr_crypto_hash_t *hash,
                                      unsigned char *result);

/* FIXME: make this opaque */
struct apr_crypto_hash_t {
    apr_crypto_hash_init_t *init;
    apr_crypto_hash_add_t *add;
    apr_crypto_hash_finish_t *finish;
    apr_size_t size;
    void *data;
};

APR_DECLARE(apr_crypto_hash_t *) apr_crypto_sha256_new(apr_pool_t *p);

typedef struct apr_random_t apr_random_t;

APR_DECLARE(void) apr_random_init(apr_random_t *g,apr_pool_t *p,
                                  apr_crypto_hash_t *pool_hash,
                                  apr_crypto_hash_t *key_hash,
                                  apr_crypto_hash_t *prng_hash);
APR_DECLARE(apr_random_t *) apr_random_standard_new(apr_pool_t *p);
APR_DECLARE(void) apr_random_add_entropy(apr_random_t *g,
                                         const void *entropy_,
                                         apr_size_t bytes);
APR_DECLARE(apr_status_t) apr_random_insecure_bytes(apr_random_t *g,
                                                    void *random,
                                                    apr_size_t bytes);
APR_DECLARE(apr_status_t) apr_random_secure_bytes(apr_random_t *g,
                                                  void *random,
                                                  apr_size_t bytes);
APR_DECLARE(void) apr_random_barrier(apr_random_t *g);
APR_DECLARE(apr_status_t) apr_random_secure_ready(apr_random_t *r);
APR_DECLARE(apr_status_t) apr_random_insecure_ready(apr_random_t *r);

/* Call this in the child after forking to mix the randomness
   pools. Note that its generally a bad idea to fork a process with a
   real PRNG in it - better to have the PRNG externally and get the
   randomness from there. However, if you really must do it, then you
   should supply all your entropy to all the PRNGs - don't worry, they
   won't produce the same output.

   Note that apr_proc_fork() calls this for you, so only weird
   applications need ever call it themselves.
*/
struct apr_proc_t;
APR_DECLARE(void) apr_random_after_fork(struct apr_proc_t *proc);

#endif /* ndef APR_RANDOM_H */
