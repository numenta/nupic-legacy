#ifndef BOOST_THREAD_PTHREAD_THREAD_DATA_HPP
#define BOOST_THREAD_PTHREAD_THREAD_DATA_HPP
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
// (C) Copyright 2007 Anthony Williams
// (C) Copyright 2011-2012 Vicente J. Botet Escriba

#include <boost/thread/detail/config.hpp>
#include <boost/thread/exceptions.hpp>
#include <boost/thread/locks.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/pthread/condition_variable_fwd.hpp>

#include <boost/shared_ptr.hpp>
#include <boost/enable_shared_from_this.hpp>
#include <boost/optional.hpp>
#include <boost/assert.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#endif

#include <map>
#include <vector>
#include <utility>

#include <pthread.h>
#include <unistd.h>

#include <boost/config/abi_prefix.hpp>

namespace boost
{
    class thread_attributes {
    public:
        thread_attributes() BOOST_NOEXCEPT {
            int res = pthread_attr_init(&val_);
            BOOST_VERIFY(!res && "pthread_attr_init failed");
        }
        ~thread_attributes() {
          int res = pthread_attr_destroy(&val_);
          BOOST_VERIFY(!res && "pthread_attr_destroy failed");
        }
        // stack
        void set_stack_size(std::size_t size) BOOST_NOEXCEPT {
          if (size==0) return;
          std::size_t page_size = getpagesize();
#ifdef PTHREAD_STACK_MIN
          if (size<PTHREAD_STACK_MIN) size=PTHREAD_STACK_MIN;
#endif
          size = ((size+page_size-1)/page_size)*page_size;
          int res = pthread_attr_setstacksize(&val_, size);
          BOOST_VERIFY(!res && "pthread_attr_setstacksize failed");
        }

        std::size_t get_stack_size() const BOOST_NOEXCEPT {
            std::size_t size;
            int res = pthread_attr_getstacksize(&val_, &size);
            BOOST_VERIFY(!res && "pthread_attr_getstacksize failed");
            return size;
        }
#define BOOST_THREAD_DEFINES_THREAD_ATTRIBUTES_NATIVE_HANDLE

        typedef pthread_attr_t native_handle_type;
        native_handle_type* native_handle() BOOST_NOEXCEPT {
          return &val_;
        }
        const native_handle_type* native_handle() const BOOST_NOEXCEPT {
          return &val_;
        }

    private:
        pthread_attr_t val_;
    };

    class thread;

    namespace detail
    {
        struct tss_cleanup_function;
        struct thread_exit_callback_node;
        struct tss_data_node
        {
            boost::shared_ptr<boost::detail::tss_cleanup_function> func;
            void* value;

            tss_data_node(boost::shared_ptr<boost::detail::tss_cleanup_function> func_,
                          void* value_):
                func(func_),value(value_)
            {}
        };

        struct thread_data_base;
        typedef boost::shared_ptr<thread_data_base> thread_data_ptr;

        struct BOOST_THREAD_DECL thread_data_base:
            enable_shared_from_this<thread_data_base>
        {
            thread_data_ptr self;
            pthread_t thread_handle;
            boost::mutex data_mutex;
            boost::condition_variable done_condition;
            boost::mutex sleep_mutex;
            boost::condition_variable sleep_condition;
            bool done;
            bool join_started;
            bool joined;
            boost::detail::thread_exit_callback_node* thread_exit_callbacks;
            std::map<void const*,boost::detail::tss_data_node> tss_data;
            bool interrupt_enabled;
            bool interrupt_requested;
            pthread_mutex_t* cond_mutex;
            pthread_cond_t* current_cond;
            typedef std::vector<std::pair<condition_variable*, mutex*>
            //, hidden_allocator<std::pair<condition_variable*, mutex*> >
            > notify_list_t;
            notify_list_t notify;

            thread_data_base():
                done(false),join_started(false),joined(false),
                thread_exit_callbacks(0),
                interrupt_enabled(true),
                interrupt_requested(false),
                current_cond(0),
                notify()
            {}
            virtual ~thread_data_base();

            typedef pthread_t native_handle_type;

            virtual void run()=0;
            void notify_all_at_thread_exit(condition_variable* cv, mutex* m)
            {
              notify.push_back(std::pair<condition_variable*, mutex*>(cv, m));
            }
        };

        BOOST_THREAD_DECL thread_data_base* get_current_thread_data();

        class interruption_checker
        {
            thread_data_base* const thread_info;
            pthread_mutex_t* m;
            bool set;

            void check_for_interruption()
            {
#ifndef BOOST_NO_EXCEPTIONS
                if(thread_info->interrupt_requested)
                {
                    thread_info->interrupt_requested=false;
                    throw thread_interrupted(); // BOOST_NO_EXCEPTIONS protected
                }
#endif
            }

            void operator=(interruption_checker&);
        public:
            explicit interruption_checker(pthread_mutex_t* cond_mutex,pthread_cond_t* cond):
                thread_info(detail::get_current_thread_data()),m(cond_mutex),
                set(thread_info && thread_info->interrupt_enabled)
            {
                if(set)
                {
                    lock_guard<mutex> guard(thread_info->data_mutex);
                    check_for_interruption();
                    thread_info->cond_mutex=cond_mutex;
                    thread_info->current_cond=cond;
                    BOOST_VERIFY(!pthread_mutex_lock(m));
                }
                else
                {
                    BOOST_VERIFY(!pthread_mutex_lock(m));
                }
            }
            ~interruption_checker()
            {
                if(set)
                {
                    BOOST_VERIFY(!pthread_mutex_unlock(m));
                    lock_guard<mutex> guard(thread_info->data_mutex);
                    thread_info->cond_mutex=NULL;
                    thread_info->current_cond=NULL;
                }
                else
                {
                    BOOST_VERIFY(!pthread_mutex_unlock(m));
                }
            }
        };
    }

    namespace this_thread
    {
#ifdef BOOST_THREAD_USES_CHRONO
        inline
        void BOOST_SYMBOL_VISIBLE sleep_for(const chrono::nanoseconds& ns)
        {
            using namespace chrono;
            boost::detail::thread_data_base* const thread_info=boost::detail::get_current_thread_data();

            if(thread_info)
            {
              unique_lock<mutex> lk(thread_info->sleep_mutex);
              while(cv_status::no_timeout==thread_info->sleep_condition.wait_for(lk,ns)) {}
            }
            else
            {
              if (ns >= nanoseconds::zero())
              {

  #   if defined(BOOST_HAS_PTHREAD_DELAY_NP)
                timespec ts;
                ts.tv_sec = static_cast<long>(duration_cast<seconds>(ns).count());
                ts.tv_nsec = static_cast<long>((ns - seconds(ts.tv_sec)).count());
                BOOST_VERIFY(!pthread_delay_np(&ts));
  #   elif defined(BOOST_HAS_NANOSLEEP)
                timespec ts;
                ts.tv_sec = static_cast<long>(duration_cast<seconds>(ns).count());
                ts.tv_nsec = static_cast<long>((ns - seconds(ts.tv_sec)).count());
                //  nanosleep takes a timespec that is an offset, not
                //  an absolute time.
                nanosleep(&ts, 0);
  #   else
                mutex mx;
                mutex::scoped_lock lock(mx);
                condition_variable cond;
                cond.wait_for(lock, ns);
  #   endif
              }
            }
        }
#endif
        void BOOST_THREAD_DECL yield() BOOST_NOEXCEPT;

#ifdef __DECXXX
        /// Workaround of DECCXX issue of incorrect template substitution
        template<typename TimeDuration>
        inline void sleep(TimeDuration const& rel_time)
        {
            this_thread::sleep(get_system_time()+rel_time);
        }

        template<>
        void BOOST_THREAD_DECL sleep(system_time const& abs_time);
#else
        void BOOST_THREAD_DECL sleep(system_time const& abs_time);

        template<typename TimeDuration>
        inline BOOST_SYMBOL_VISIBLE void sleep(TimeDuration const& rel_time)
        {
            this_thread::sleep(get_system_time()+rel_time);
        }
#endif
    }
}

#include <boost/config/abi_suffix.hpp>

#endif
