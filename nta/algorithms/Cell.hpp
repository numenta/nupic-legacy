/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
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

#ifndef NTA_CELL_HPP
#define NTA_CELL_HPP

#include <vector>
#include <nta/types/types.hpp>
#include <nta/algorithms/Segment.hpp>

namespace nta {
  namespace algorithms {
    namespace Cells4 {

      class Cells4;

      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      /**
       * A Cell is a container for Segments. It maintains a list of active segments and
       * a list of segments that have been "inactivated" because all their synapses were
       * removed. The slots of inactivated segments are re-used, in contrast to the
       * Python TP, which keeps its segments in a dynamic list and always allocates new
       * segments at the end of this dynamic list. This difference is a source of
       * mismatches in unit testing when comparing the Python TP to the C++ down to the
       * segment level.
       */
      class Cell
      {
      private:
        std::vector< Segment >   _segments;     // both 'active' and 'inactive' segments
        std::vector<UInt> _freeSegments; // slots of the 'inactive' segments

      public:
        //--------------------------------------------------------------------------------
        Cell();

        //--------------------------------------------------------------------------------
        bool empty() const { return _segments.size() == _freeSegments.size(); }

        //--------------------------------------------------------------------------------
        UInt nSynapses() const
        {
          UInt n = 0;
          for (UInt i = 0; i != _segments.size(); ++i)
            n += _segments[i].size();
          return n;
        }

        //--------------------------------------------------------------------------------
        /**
         * Returns size of _segments (see nSegments below). If using this to iterate,
         * indices less than size() might contain indices of empty segments.
         */
        UInt size() const { return _segments.size(); }

        //--------------------------------------------------------------------------------
        /**
         * Returns number of segments that are not in the free list currently, i.e. that
         * have at leat 1 synapse.
         */
        UInt nSegments() const
        {
          NTA_ASSERT(_freeSegments.size() <= _segments.size());
          return _segments.size() - _freeSegments.size();
        }

        //--------------------------------------------------------------------------------
        /**
         * Returns list of segments that are not empty.
         */
        std::vector<UInt> getNonEmptySegList() const
        {
          std::vector<UInt> non_empties;
          for (UInt i = 0; i != _segments.size(); ++i)
            if (!_segments[i].empty())
              non_empties.push_back(i);
          NTA_ASSERT(non_empties.size() == nSegments());
          return non_empties;
        }

        //--------------------------------------------------------------------------------
        Segment& operator[](UInt segIdx)
        {
          NTA_ASSERT(segIdx < _segments.size());
          return _segments[segIdx];
        }

        //--------------------------------------------------------------------------------
        const Segment& operator[](UInt segIdx) const
        {
          NTA_ASSERT(segIdx < _segments.size());
          return _segments[segIdx];
        }

        //--------------------------------------------------------------------------------
        Segment& getSegment(UInt segIdx)
        {
          NTA_ASSERT(segIdx < _segments.size());
          return _segments[segIdx];
        }

        //--------------------------------------------------------------------------------
        /**
         * Returns an empty segment to use, either from list of already
         * allocated ones that have been previously "freed" (but we kept
         * the memory allocated), or by allocating a new one.
         */
        // TODO: rename method to "addToFreeSegment" ??
        UInt getFreeSegment(const Segment::InSynapses& synapses,
                            Real initFrequency,
                            bool sequenceSegmentFlag,
                            Real permConnected,
                            UInt iteration);

        //--------------------------------------------------------------------------------
        /**
         *  Whether we  want to match python's segment ordering
         */
        static void setSegmentOrder(bool matchPythonOrder);


        //--------------------------------------------------------------------------------
        /**
         * Update the duty cycle of each segment in this cell
         */
        void updateDutyCycle(UInt iterations);

        //--------------------------------------------------------------------------------
        /**
         * Rebalance the segment list. The segment list is compacted and all
         * free segments are removed. The most frequent segment is placed at
         * the head of the list.
         *
         * Note: outSynapses must be updated after a call to this.
         */
        void rebalanceSegments()
        {
          //const std::vector<UInt> &non_empties = getNonEmptySegList();
          UInt bestOne = getMostActiveSegment();

          // Swap the best one with the 0'th one
          if (bestOne != 0) {
            Segment seg = _segments[0];
            _segments[0] = _segments[bestOne];
            _segments[bestOne] = seg;
          }

          // Sort segments according to activation frequency

          // Redo free segments list
          _freeSegments.clear();
          for (UInt segIdx = 0; segIdx != _segments.size(); ++segIdx) {
            if ( _segments[segIdx].empty() )
              releaseSegment(segIdx);
          }
        }

        //--------------------------------------------------------------------------------
        /**
         * Returns index of segment with highest activation frequency.
         * 0 means
         */
        UInt getMostActiveSegment()
        {
          UInt bestIdx = 0;       // Segment with highest totalActivations
          UInt maxActivity = 0;   // Value of highest totalActivations

          for (UInt i = 0; i < _segments.size(); ++i) {
            if ( !_segments[i].empty() &&
                 (_segments[i].getTotalActivations() > maxActivity) ){
              maxActivity = _segments[i].getTotalActivations();
              bestIdx = i;
            }
          }

          return bestIdx;
        }
        //--------------------------------------------------------------------------------
        /**
         * Release a segment by putting it on the list of "freed" segments. We keep the
         * memory instead of deallocating it each time, so that's it's fast to "allocate"
         * a new segment next time.
         *
         * Assumes outSynapses has already been updated.
         * TODO: a call to releaseSegment should delete any pending
         *       update for that segment in the update list. The
         *       cheapest way to do this is to maintain segment updates on a
         *       per cell basis.  Currently there is a check in
         *       Cells4::adaptSegment for this case but that may be insufficient.
         */
        void releaseSegment(UInt segIdx)
        {
          NTA_ASSERT(segIdx < _segments.size());

          // TODO: check this
          if (is_in(segIdx, _freeSegments)) {
            return;
          }

          // TODO: check this
          NTA_ASSERT(not_in(segIdx, _freeSegments));

          _segments[segIdx].clear(); // important in case we push_back later
          _freeSegments.push_back(segIdx);
          _segments[segIdx]._totalActivations = 0;
          _segments[segIdx]._positiveActivations = 0;

          NTA_ASSERT(_segments[segIdx].empty());
          NTA_ASSERT(is_in(segIdx, _freeSegments));
        }

        // The comment below is so awesome, I had to leave it in!

        //----------------------------------------------------------------------
        /**
         * TODO: write
         */
        bool invariants(Cells4* =NULL) const
        {
          return true;
        }

        //----------------------------------------------------------------------
        // PERSISTENCE
        //----------------------------------------------------------------------
        UInt persistentSize() const
        {
          std::stringstream buff;
          this->save(buff);
          return buff.str().size();
        }

        //----------------------------------------------------------------------
        void save(std::ostream& outStream) const;

        //----------------------------------------------------------------------
        void load(std::istream& inStream);

      };

      // end namespace
    }
  }
}
#endif // NTA_CELL_HPP

