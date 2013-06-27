//  lock-free single-producer/single-consumer ringbuffer
//  this algorithm is implemented in various projects (linux kernel)
//
//  Copyright (C) 2009, 2011 Tim Blechmann
//
//  Distributed under the Boost Software License, Version 1.0. (See
//  accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#ifndef BOOST_LOCKFREE_SPSC_QUEUE_HPP_INCLUDED
#define BOOST_LOCKFREE_SPSC_QUEUE_HPP_INCLUDED

#include <algorithm>

#include <boost/array.hpp>
#include <boost/assert.hpp>
#include <boost/noncopyable.hpp>
#include <boost/static_assert.hpp>

#include <boost/lockfree/detail/atomic.hpp>
#include <boost/lockfree/detail/branch_hints.hpp>
#include <boost/lockfree/detail/parameter.hpp>
#include <boost/lockfree/detail/prefix.hpp>


namespace boost    {
namespace lockfree {
namespace detail   {

typedef parameter::parameters<boost::parameter::optional<tag::capacity>,
                              boost::parameter::optional<tag::allocator>
                             > ringbuffer_signature;

template <typename T>
class ringbuffer_base:
    boost::noncopyable
{
#ifndef BOOST_DOXYGEN_INVOKED
    typedef std::size_t size_t;
    static const int padding_size = BOOST_LOCKFREE_CACHELINE_BYTES - sizeof(size_t);
    atomic<size_t> write_index_;
    char padding1[padding_size]; /* force read_index and write_index to different cache lines */
    atomic<size_t> read_index_;

protected:
    ringbuffer_base(void):
        write_index_(0), read_index_(0)
    {}

    static size_t next_index(size_t arg, size_t max_size)
    {
        size_t ret = arg + 1;
        while (unlikely(ret >= max_size))
            ret -= max_size;
        return ret;
    }

    static size_t read_available(size_t write_index, size_t read_index, size_t max_size)
    {
        if (write_index >= read_index)
            return write_index - read_index;

        size_t ret = write_index + max_size - read_index;
        return ret;
    }

    static size_t write_available(size_t write_index, size_t read_index, size_t max_size)
    {
        size_t ret = read_index - write_index - 1;
        if (write_index >= read_index)
            ret += max_size;
        return ret;
    }

    bool push(T const & t, T * buffer, size_t max_size)
    {
        size_t write_index = write_index_.load(memory_order_relaxed);  // only written from push thread
        size_t next = next_index(write_index, max_size);

        if (next == read_index_.load(memory_order_acquire))
            return false; /* ringbuffer is full */

        buffer[write_index] = t;

        write_index_.store(next, memory_order_release);

        return true;
    }

    size_t push(const T * input_buffer, size_t input_count, T * internal_buffer, size_t max_size)
    {
        size_t write_index = write_index_.load(memory_order_relaxed);  // only written from push thread
        const size_t read_index  = read_index_.load(memory_order_acquire);
        const size_t avail = write_available(write_index, read_index, max_size);

        if (avail == 0)
            return 0;

        input_count = (std::min)(input_count, avail);

        size_t new_write_index = write_index + input_count;

        if (write_index + input_count > max_size) {
            /* copy data in two sections */
            size_t count0 = max_size - write_index;

            std::copy(input_buffer, input_buffer + count0, internal_buffer + write_index);
            std::copy(input_buffer + count0, input_buffer + input_count, internal_buffer);
            new_write_index -= max_size;
        } else {
            std::copy(input_buffer, input_buffer + input_count, internal_buffer + write_index);

            if (new_write_index == max_size)
                new_write_index = 0;
        }

        write_index_.store(new_write_index, memory_order_release);
        return input_count;
    }

    template <typename ConstIterator>
    ConstIterator push(ConstIterator begin, ConstIterator end, T * internal_buffer, size_t max_size)
    {
        // FIXME: avoid std::distance and std::advance

        size_t write_index = write_index_.load(memory_order_relaxed);  // only written from push thread
        const size_t read_index  = read_index_.load(memory_order_acquire);
        const size_t avail = write_available(write_index, read_index, max_size);

        if (avail == 0)
            return begin;

        size_t input_count = std::distance(begin, end);
        input_count = (std::min)(input_count, avail);

        size_t new_write_index = write_index + input_count;

        ConstIterator last = begin;
        std::advance(last, input_count);

        if (write_index + input_count > max_size) {
            /* copy data in two sections */
            size_t count0 = max_size - write_index;
            ConstIterator midpoint = begin;
            std::advance(midpoint, count0);

            std::copy(begin, midpoint, internal_buffer + write_index);
            std::copy(midpoint, last, internal_buffer);
            new_write_index -= max_size;
        } else {
            std::copy(begin, last, internal_buffer + write_index);

            if (new_write_index == max_size)
                new_write_index = 0;
        }

        write_index_.store(new_write_index, memory_order_release);
        return last;
    }

    bool pop (T & ret, T * buffer, size_t max_size)
    {
        size_t write_index = write_index_.load(memory_order_acquire);
        size_t read_index  = read_index_.load(memory_order_relaxed); // only written from pop thread
        if (empty(write_index, read_index))
            return false;

        ret = buffer[read_index];
        size_t next = next_index(read_index, max_size);
        read_index_.store(next, memory_order_release);
        return true;
    }

    size_t pop (T * output_buffer, size_t output_count, const T * internal_buffer, size_t max_size)
    {
        const size_t write_index = write_index_.load(memory_order_acquire);
        size_t read_index = read_index_.load(memory_order_relaxed); // only written from pop thread

        const size_t avail = read_available(write_index, read_index, max_size);

        if (avail == 0)
            return 0;

        output_count = (std::min)(output_count, avail);

        size_t new_read_index = read_index + output_count;

        if (read_index + output_count > max_size) {
            /* copy data in two sections */
            size_t count0 = max_size - read_index;
            size_t count1 = output_count - count0;

            std::copy(internal_buffer + read_index, internal_buffer + max_size, output_buffer);
            std::copy(internal_buffer, internal_buffer + count1, output_buffer + count0);

            new_read_index -= max_size;
        } else {
            std::copy(internal_buffer + read_index, internal_buffer + read_index + output_count, output_buffer);
            if (new_read_index == max_size)
                new_read_index = 0;
        }

        read_index_.store(new_read_index, memory_order_release);
        return output_count;
    }

    template <typename OutputIterator>
    size_t pop (OutputIterator it, const T * internal_buffer, size_t max_size)
    {
        const size_t write_index = write_index_.load(memory_order_acquire);
        size_t read_index = read_index_.load(memory_order_relaxed); // only written from pop thread

        const size_t avail = read_available(write_index, read_index, max_size);
        if (avail == 0)
            return 0;

        size_t new_read_index = read_index + avail;

        if (read_index + avail > max_size) {
            /* copy data in two sections */
            size_t count0 = max_size - read_index;
            size_t count1 = avail - count0;

            std::copy(internal_buffer + read_index, internal_buffer + max_size, it);
            std::copy(internal_buffer, internal_buffer + count1, it);

            new_read_index -= max_size;
        } else {
            std::copy(internal_buffer + read_index, internal_buffer + read_index + avail, it);
            if (new_read_index == max_size)
                new_read_index = 0;
        }

        read_index_.store(new_read_index, memory_order_release);
        return avail;
    }
#endif


public:
    /** reset the ringbuffer
     *
     * \note Not thread-safe
     * */
    void reset(void)
    {
        write_index_.store(0, memory_order_relaxed);
        read_index_.store(0, memory_order_release);
    }

    /** Check if the ringbuffer is empty
     *
     * \return true, if the ringbuffer is empty, false otherwise
     * \note Due to the concurrent nature of the ringbuffer the result may be inaccurate.
     * */
    bool empty(void)
    {
        return empty(write_index_.load(memory_order_relaxed), read_index_.load(memory_order_relaxed));
    }

    /**
     * \return true, if implementation is lock-free.
     *
     * */
    bool is_lock_free(void) const
    {
        return write_index_.is_lock_free() && read_index_.is_lock_free();
    }

private:
    bool empty(size_t write_index, size_t read_index)
    {
        return write_index == read_index;
    }
};

template <typename T, std::size_t max_size>
class compile_time_sized_ringbuffer:
    public ringbuffer_base<T>
{
    typedef std::size_t size_t;
    boost::array<T, max_size> array_;

public:
    bool push(T const & t)
    {
        return ringbuffer_base<T>::push(t, array_.c_array(), max_size);
    }

    bool pop(T & ret)
    {
        return ringbuffer_base<T>::pop(ret, array_.c_array(), max_size);
    }

    size_t push(T const * t, size_t size)
    {
        return ringbuffer_base<T>::push(t, size, array_.c_array(), max_size);
    }

    template <size_t size>
    size_t push(T const (&t)[size])
    {
        return push(t, size);
    }

    template <typename ConstIterator>
    ConstIterator push(ConstIterator begin, ConstIterator end)
    {
        return ringbuffer_base<T>::push(begin, end, array_.c_array(), max_size);
    }

    size_t pop(T * ret, size_t size)
    {
        return ringbuffer_base<T>::pop(ret, size, array_.c_array(), max_size);
    }

    template <size_t size>
    size_t pop(T (&ret)[size])
    {
        return pop(ret, size);
    }

    template <typename OutputIterator>
    size_t pop(OutputIterator it)
    {
        return ringbuffer_base<T>::pop(it, array_.c_array(), max_size);
    }
};

template <typename T, typename Alloc>
class runtime_sized_ringbuffer:
    public ringbuffer_base<T>,
    private Alloc
{
    typedef std::size_t size_t;
    size_t max_elements_;
    typedef typename Alloc::pointer pointer;
    pointer array_;

public:
    explicit runtime_sized_ringbuffer(size_t max_elements):
        max_elements_(max_elements)
    {
        // TODO: we don't necessarily need to construct all elements
        array_ = Alloc::allocate(max_elements);
        for (size_t i = 0; i != max_elements; ++i)
            Alloc::construct(array_ + i, T());
    }

    template <typename U>
    runtime_sized_ringbuffer(typename Alloc::template rebind<U>::other const & alloc, size_t max_elements):
        Alloc(alloc), max_elements_(max_elements)
    {
        // TODO: we don't necessarily need to construct all elements
        array_ = Alloc::allocate(max_elements);
        for (size_t i = 0; i != max_elements; ++i)
            Alloc::construct(array_ + i, T());
    }

    runtime_sized_ringbuffer(Alloc const & alloc, size_t max_elements):
        Alloc(alloc), max_elements_(max_elements)
    {
        // TODO: we don't necessarily need to construct all elements
        array_ = Alloc::allocate(max_elements);
        for (size_t i = 0; i != max_elements; ++i)
            Alloc::construct(array_ + i, T());
    }

    ~runtime_sized_ringbuffer(void)
    {
        for (size_t i = 0; i != max_elements_; ++i)
            Alloc::destroy(array_ + i);
        Alloc::deallocate(array_, max_elements_);
    }

    bool push(T const & t)
    {
        return ringbuffer_base<T>::push(t, &*array_, max_elements_);
    }

    bool pop(T & ret)
    {
        return ringbuffer_base<T>::pop(ret, &*array_, max_elements_);
    }

    size_t push(T const * t, size_t size)
    {
        return ringbuffer_base<T>::push(t, size, &*array_, max_elements_);
    }

    template <size_t size>
    size_t push(T const (&t)[size])
    {
        return push(t, size);
    }

    template <typename ConstIterator>
    ConstIterator push(ConstIterator begin, ConstIterator end)
    {
        return ringbuffer_base<T>::push(begin, end, array_, max_elements_);
    }

    size_t pop(T * ret, size_t size)
    {
        return ringbuffer_base<T>::pop(ret, size, array_, max_elements_);
    }

    template <size_t size>
    size_t pop(T (&ret)[size])
    {
        return pop(ret, size);
    }

    template <typename OutputIterator>
    size_t pop(OutputIterator it)
    {
        return ringbuffer_base<T>::pop(it, array_, max_elements_);
    }
};

template <typename T, typename A0, typename A1>
struct make_ringbuffer
{
    typedef typename ringbuffer_signature::bind<A0, A1>::type bound_args;

    typedef extract_capacity<bound_args> extract_capacity_t;

    static const bool runtime_sized = !extract_capacity_t::has_capacity;
    static const size_t capacity    =  extract_capacity_t::capacity;

    typedef extract_allocator<bound_args, T> extract_allocator_t;
    typedef typename extract_allocator_t::type allocator;

    // allocator argument is only sane, for run-time sized ringbuffers
    BOOST_STATIC_ASSERT((mpl::if_<mpl::bool_<!runtime_sized>,
                                  mpl::bool_<!extract_allocator_t::has_allocator>,
                                  mpl::true_
                                 >::type::value));

    typedef typename mpl::if_c<runtime_sized,
                               runtime_sized_ringbuffer<T, allocator>,
                               compile_time_sized_ringbuffer<T, capacity>
                              >::type ringbuffer_type;
};


} /* namespace detail */


/** The spsc_queue class provides a single-writer/single-reader fifo queue, pushing and popping is wait-free.
 *
 *  \b Policies:
 *  - \c boost::lockfree::capacity<>, optional <br>
 *    If this template argument is passed to the options, the size of the ringbuffer is set at compile-time.
 *
 *  - \c boost::lockfree::allocator<>, defaults to \c boost::lockfree::allocator<std::allocator<T>> <br>
 *    Specifies the allocator that is used to allocate the ringbuffer. This option is only valid, if the ringbuffer is configured
 *    to be sized at run-time
 *
 *  \b Requirements:
 *  - T must have a default constructor
 *  - T must be copyable
 * */
#ifndef BOOST_DOXYGEN_INVOKED
template <typename T,
          class A0 = boost::parameter::void_,
          class A1 = boost::parameter::void_>
#else
template <typename T, ...Options>
#endif
class spsc_queue:
    public detail::make_ringbuffer<T, A0, A1>::ringbuffer_type
{
private:

#ifndef BOOST_DOXYGEN_INVOKED
    typedef typename detail::make_ringbuffer<T, A0, A1>::ringbuffer_type base_type;
    static const bool runtime_sized = detail::make_ringbuffer<T, A0, A1>::runtime_sized;
    typedef typename detail::make_ringbuffer<T, A0, A1>::allocator allocator_arg;

    struct implementation_defined
    {
        typedef allocator_arg allocator;
        typedef std::size_t size_type;
    };
#endif

public:
    typedef T value_type;
    typedef typename implementation_defined::allocator allocator;
    typedef typename implementation_defined::size_type size_type;

    /** Constructs a spsc_queue
     *
     *  \pre spsc_queue must be configured to be sized at compile-time
     */
    // @{
    spsc_queue(void)
    {
        BOOST_ASSERT(!runtime_sized);
    }

    template <typename U>
    explicit spsc_queue(typename allocator::template rebind<U>::other const & alloc)
    {
        // just for API compatibility: we don't actually need an allocator
        BOOST_STATIC_ASSERT(!runtime_sized);
    }

    explicit spsc_queue(allocator const & alloc)
    {
        // just for API compatibility: we don't actually need an allocator
        BOOST_ASSERT(!runtime_sized);
    }
    // @}


    /** Constructs a spsc_queue for element_count elements
     *
     *  \pre spsc_queue must be configured to be sized at run-time
     */
    // @{
    explicit spsc_queue(size_type element_count):
        base_type(element_count)
    {
        BOOST_ASSERT(runtime_sized);
    }

    template <typename U>
    spsc_queue(size_type element_count, typename allocator::template rebind<U>::other const & alloc):
        base_type(alloc, element_count)
    {
        BOOST_STATIC_ASSERT(runtime_sized);
    }

    spsc_queue(size_type element_count, allocator_arg const & alloc):
        base_type(alloc, element_count)
    {
        BOOST_ASSERT(runtime_sized);
    }
    // @}

    /** Pushes object t to the ringbuffer.
     *
     * \pre only one thread is allowed to push data to the spsc_queue
     * \post object will be pushed to the spsc_queue, unless it is full.
     * \return true, if the push operation is successful.
     *
     * \note Thread-safe and wait-free
     * */
    bool push(T const & t)
    {
        return base_type::push(t);
    }

    /** Pops one object from ringbuffer.
     *
     * \pre only one thread is allowed to pop data to the spsc_queue
     * \post if ringbuffer is not empty, object will be copied to ret.
     * \return true, if the pop operation is successful, false if ringbuffer was empty.
     *
     * \note Thread-safe and wait-free
     */
    bool pop(T & ret)
    {
        return base_type::pop(ret);
    }

    /** Pushes as many objects from the array t as there is space.
     *
     * \pre only one thread is allowed to push data to the spsc_queue
     * \return number of pushed items
     *
     * \note Thread-safe and wait-free
     */
    size_type push(T const * t, size_type size)
    {
        return base_type::push(t, size);
    }

    /** Pushes as many objects from the array t as there is space available.
     *
     * \pre only one thread is allowed to push data to the spsc_queue
     * \return number of pushed items
     *
     * \note Thread-safe and wait-free
     */
    template <size_type size>
    size_type push(T const (&t)[size])
    {
        return push(t, size);
    }

    /** Pushes as many objects from the range [begin, end) as there is space .
     *
     * \pre only one thread is allowed to push data to the spsc_queue
     * \return iterator to the first element, which has not been pushed
     *
     * \note Thread-safe and wait-free
     */
    template <typename ConstIterator>
    ConstIterator push(ConstIterator begin, ConstIterator end)
    {
        return base_type::push(begin, end);
    }

    /** Pops a maximum of size objects from ringbuffer.
     *
     * \pre only one thread is allowed to pop data to the spsc_queue
     * \return number of popped items
     *
     * \note Thread-safe and wait-free
     * */
    size_type pop(T * ret, size_type size)
    {
        return base_type::pop(ret, size);
    }

    /** Pops a maximum of size objects from spsc_queue.
     *
     * \pre only one thread is allowed to pop data to the spsc_queue
     * \return number of popped items
     *
     * \note Thread-safe and wait-free
     * */
    template <size_type size>
    size_type pop(T (&ret)[size])
    {
        return pop(ret, size);
    }

    /** Pops objects to the output iterator it
     *
     * \pre only one thread is allowed to pop data to the spsc_queue
     * \return number of popped items
     *
     * \note Thread-safe and wait-free
     * */
    template <typename OutputIterator>
    size_type pop(OutputIterator it)
    {
        return base_type::pop(it);
    }
};

} /* namespace lockfree */
} /* namespace boost */


#endif /* BOOST_LOCKFREE_SPSC_QUEUE_HPP_INCLUDED */
