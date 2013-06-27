// Boost.Geometry (aka GGL, Generic Geometry Library)

// Copyright (c) 2007-2012 Barend Gehrels, Amsterdam, the Netherlands.

// Use, modification and distribution is subject to the Boost Software License,
// Version 1.0. (See accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)

#ifndef BOOST_GEOMETRY_MULTI_ALGORITHMS_INTERSECTION_HPP
#define BOOST_GEOMETRY_MULTI_ALGORITHMS_INTERSECTION_HPP


#include <boost/geometry/multi/core/closure.hpp>
#include <boost/geometry/multi/core/geometry_id.hpp>
#include <boost/geometry/multi/core/is_areal.hpp>
#include <boost/geometry/multi/core/point_order.hpp>
#include <boost/geometry/multi/algorithms/covered_by.hpp>
#include <boost/geometry/multi/algorithms/envelope.hpp>
#include <boost/geometry/multi/algorithms/num_points.hpp>
#include <boost/geometry/multi/algorithms/detail/overlay/get_ring.hpp>
#include <boost/geometry/multi/algorithms/detail/overlay/get_turns.hpp>
#include <boost/geometry/multi/algorithms/detail/overlay/copy_segments.hpp>
#include <boost/geometry/multi/algorithms/detail/overlay/copy_segment_point.hpp>
#include <boost/geometry/multi/algorithms/detail/overlay/select_rings.hpp>
#include <boost/geometry/multi/algorithms/detail/sections/range_by_section.hpp>
#include <boost/geometry/multi/algorithms/detail/sections/sectionalize.hpp>

#include <boost/geometry/algorithms/intersection.hpp>


namespace boost { namespace geometry
{

#ifndef DOXYGEN_NO_DETAIL
namespace detail { namespace intersection
{


template
<
    typename MultiLinestring1, typename MultiLinestring2,
    typename OutputIterator, typename PointOut,
    typename Strategy
>
struct intersection_multi_linestring_multi_linestring_point
{
    static inline OutputIterator apply(MultiLinestring1 const& ml1,
            MultiLinestring2 const& ml2, OutputIterator out,
            Strategy const& strategy)
    {
        // Note, this loop is quadratic w.r.t. number of linestrings per input.
        // Future Enhancement: first do the sections of each, then intersect.
        for (typename boost::range_iterator
                <
                    MultiLinestring1 const
                >::type it1 = boost::begin(ml1);
            it1 != boost::end(ml1);
            ++it1)
        {
            for (typename boost::range_iterator
                    <
                        MultiLinestring2 const
                    >::type it2 = boost::begin(ml2);
                it2 != boost::end(ml2);
                ++it2)
            {
                out = intersection_linestring_linestring_point
                    <
                        typename boost::range_value<MultiLinestring1>::type,
                        typename boost::range_value<MultiLinestring2>::type,
                        OutputIterator, PointOut, Strategy
                    >::apply(*it1, *it2, out, strategy);
            }
        }

        return out;
    }
};


template
<
    typename Linestring, typename MultiLinestring,
    typename OutputIterator, typename PointOut,
    typename Strategy
>
struct intersection_linestring_multi_linestring_point
{
    static inline OutputIterator apply(Linestring const& linestring,
            MultiLinestring const& ml, OutputIterator out,
            Strategy const& strategy)
    {
        for (typename boost::range_iterator
                <
                    MultiLinestring const
                >::type it = boost::begin(ml);
            it != boost::end(ml);
            ++it)
        {
            out = intersection_linestring_linestring_point
                <
                    Linestring,
                    typename boost::range_value<MultiLinestring>::type,
                    OutputIterator, PointOut, Strategy
                >::apply(linestring, *it, out, strategy);
        }

        return out;
    }
};


// This loop is quite similar to the loop above, but beacuse the iterator
// is second (above) or first (below) argument, it is not trivial to merge them.
template
<
    typename MultiLinestring, typename Areal,
    bool ReverseAreal,
    typename OutputIterator, typename LineStringOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_of_multi_linestring_with_areal
{
    static inline OutputIterator apply(MultiLinestring const& ml, Areal const& areal,
            OutputIterator out,
            Strategy const& strategy)
    {
        for (typename boost::range_iterator
                <
                    MultiLinestring const
                >::type it = boost::begin(ml);
            it != boost::end(ml);
            ++it)
        {
            out = intersection_of_linestring_with_areal
                <
                    typename boost::range_value<MultiLinestring>::type,
                    Areal, ReverseAreal,
                    OutputIterator, LineStringOut, OverlayType, Strategy
                >::apply(*it, areal, out, strategy);
        }

        return out;

    }
};

// This one calls the one above with reversed arguments
template
<
    typename Areal, typename MultiLinestring,
    bool ReverseAreal,
    typename OutputIterator, typename LineStringOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_of_areal_with_multi_linestring
{
    static inline OutputIterator apply(Areal const& areal, MultiLinestring const& ml,
            OutputIterator out,
            Strategy const& strategy)
    {
        return intersection_of_multi_linestring_with_areal
            <
                MultiLinestring, Areal, ReverseAreal,
                OutputIterator, LineStringOut,
                OverlayType,
                Strategy
            >::apply(ml, areal, out, strategy);
    }
};



template
<
    typename MultiLinestring, typename Box,
    typename OutputIterator, typename LinestringOut,
    typename Strategy
>
struct clip_multi_linestring
{
    static inline OutputIterator apply(MultiLinestring const& multi_linestring,
            Box const& box, OutputIterator out, Strategy const& )
    {
        typedef typename point_type<LinestringOut>::type point_type;
        strategy::intersection::liang_barsky<Box, point_type> lb_strategy;
        for (typename boost::range_iterator<MultiLinestring const>::type it
            = boost::begin(multi_linestring);
            it != boost::end(multi_linestring); ++it)
        {
            out = detail::intersection::clip_range_with_box
                <LinestringOut>(box, *it, out, lb_strategy);
        }
        return out;
    }
};


}} // namespace detail::intersection
#endif // DOXYGEN_NO_DETAIL


#ifndef DOXYGEN_NO_DISPATCH
namespace dispatch
{


// Linear
template
<
    typename MultiLinestring1, typename MultiLinestring2,
    bool Reverse1, bool Reverse2, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        multi_linestring_tag, multi_linestring_tag, point_tag,
        false, false, false,
        MultiLinestring1, MultiLinestring2,
        Reverse1, Reverse2, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_multi_linestring_multi_linestring_point
            <
                MultiLinestring1, MultiLinestring2,
                OutputIterator, GeometryOut,
                Strategy
            >
{};


template
<
    typename Linestring, typename MultiLinestring,
    typename OutputIterator, typename GeometryOut,
    bool Reverse1, bool Reverse2, bool ReverseOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        linestring_tag, multi_linestring_tag, point_tag,
        false, false, false,
        Linestring, MultiLinestring,
        Reverse1, Reverse2, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_linestring_multi_linestring_point
            <
                Linestring, MultiLinestring,
                OutputIterator, GeometryOut,
                Strategy
            >
{};


template
<
    typename MultiLinestring, typename Box,
    bool Reverse1, bool Reverse2, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        multi_linestring_tag, box_tag, linestring_tag,
        false, true, false,
        MultiLinestring, Box,
        Reverse1, Reverse2, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::clip_multi_linestring
            <
                MultiLinestring, Box,
                OutputIterator, GeometryOut,
                Strategy
            >
{};


template
<
    typename Linestring, typename MultiPolygon,
    bool ReverseLinestring, bool ReverseMultiPolygon, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        linestring_tag, multi_polygon_tag, linestring_tag,
        false, true, false,
        Linestring, MultiPolygon,
        ReverseLinestring, ReverseMultiPolygon, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_of_linestring_with_areal
            <
                Linestring, MultiPolygon,
                ReverseMultiPolygon,
                OutputIterator, GeometryOut,
                OverlayType,
                Strategy
            >
{};


// Derives from areal/mls because runtime arguments are in that order.
// areal/mls reverses it itself to mls/areal
template
<
    typename Polygon, typename MultiLinestring,
    bool ReversePolygon, bool ReverseMultiLinestring, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        polygon_tag, multi_linestring_tag, linestring_tag,
        true, false, false,
        Polygon, MultiLinestring,
        ReversePolygon, ReverseMultiLinestring, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_of_areal_with_multi_linestring
            <
                Polygon, MultiLinestring,
                ReversePolygon,
                OutputIterator, GeometryOut,
                OverlayType,
                Strategy
            >
{};


template
<
    typename MultiLinestring, typename Ring,
    bool ReverseMultiLinestring, bool ReverseRing, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        multi_linestring_tag, ring_tag, linestring_tag,
        false, true, false,
        MultiLinestring, Ring,
        ReverseMultiLinestring, ReverseRing, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_of_multi_linestring_with_areal
            <
                MultiLinestring, Ring,
                ReverseRing,
                OutputIterator, GeometryOut,
                OverlayType,
                Strategy
            >
{};

template
<
    typename MultiLinestring, typename Polygon,
    bool ReverseMultiLinestring, bool ReverseRing, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        multi_linestring_tag, polygon_tag, linestring_tag,
        false, true, false,
        MultiLinestring, Polygon,
        ReverseMultiLinestring, ReverseRing, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_of_multi_linestring_with_areal
            <
                MultiLinestring, Polygon,
                ReverseRing,
                OutputIterator, GeometryOut,
                OverlayType,
                Strategy
            >
{};



template
<
    typename MultiLinestring, typename MultiPolygon,
    bool ReverseMultiLinestring, bool ReverseMultiPolygon, bool ReverseOut,
    typename OutputIterator, typename GeometryOut,
    overlay_type OverlayType,
    typename Strategy
>
struct intersection_insert
    <
        multi_linestring_tag, multi_polygon_tag, linestring_tag,
        false, true, false,
        MultiLinestring, MultiPolygon,
        ReverseMultiLinestring, ReverseMultiPolygon, ReverseOut,
        OutputIterator, GeometryOut,
        OverlayType,
        Strategy
    > : detail::intersection::intersection_of_multi_linestring_with_areal
            <
                MultiLinestring, MultiPolygon,
                ReverseMultiPolygon,
                OutputIterator, GeometryOut,
                OverlayType,
                Strategy
            >
{};


} // namespace dispatch
#endif

}} // namespace boost::geometry


#endif // BOOST_GEOMETRY_MULTI_ALGORITHMS_INTERSECTION_HPP

