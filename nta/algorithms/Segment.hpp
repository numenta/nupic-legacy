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

#ifndef NTA_SEGMENT_HPP
#define NTA_SEGMENT_HPP

#include <algorithm>
#include <cstring>
#include <fstream>
#include <istream>
#include <ostream>
#include <set>
#include <vector>

#include <nta/math/array_algo.hpp> // is_sorted
#include <nta/math/stl_io.hpp> // binary_save
#include <nta/algorithms/InSynapse.hpp>


//-----------------------------------------------------------------------
/**
    Overview
    ========

    The Segment class implements a single segment on a cell. It contains a list
    of incoming synapses, a sequence segment flag, and meta information about
    segment activity and duty cycle.

    There are a number of metrics representing segment activity. These include
    the total activations, the number of positive activations, the last
    iteration on which the segment became active, and the overall duty cycle.
    These metrics are used to calculate confidence levels of temporal pooler
    predictions. They are also used in fixed resource CLA and online learning to
    determine which segments and synapses to discard when the cell or segment
    reaches capacity.

    There is a reasonable correspondence to the Python Segment class and most
    of the methods here are accessible from Python.

    Implementation Notes
    ====================

    It is valid to have an empty segment. Empty segments are used in the Cell
    class to avoid always shuffling the list of segments whenever a segment is
    deleted.

    A Segment stores synapses in an STL vector of InSynapses. Synapses are
    unique on the segment, and they are kept in order of increasing source cell
    index for speed of certain operations.

    There are a list of duty cycle "tiers". These are iteration counts at which
    different alpha values are used to update the duty cycle. This is necessary
    for implementing a fast moving average, while allowing high precision. It
    is important that the duty cycle tiers are identical between Python and
    CPP implementations.

    The member variable _nConnected holds the number of synapses that
    are actually connected (permanence value >= connected threshold).

 */

//-----------------------------------------------------------------------

namespace nta {
  namespace algorithms {
    namespace Cells4 {

      //-----------------------------------------------------------------------
      /**
       * Encapsulate the arrays used to maintain per-cell state.
       */
      class CState
      {
      public:
        static const UInt VERSION = 2;

        CState()
        {
          _nCells = 0;
          _pData = NULL;
          _fMemoryAllocatedByPython = false;
          _version = VERSION;
        }
        ~CState()
        {
          if (_fMemoryAllocatedByPython == false  &&  _pData != NULL)
            delete [] _pData;
        }
        CState& operator=(const CState& o)
        {
          NTA_ASSERT(_nCells == o._nCells); // _nCells should be static, since it is the same size for all CStates
          memcpy(_pData, o._pData, _nCells);
          return *this;
        }
        bool initialize(const UInt nCells)
        {
          if (_nCells != 0)                 // if already initialized
            return false;                   // don't do it again
          if (nCells == 0)                  // if a bogus value
            return false;                   // bail out
          _nCells = nCells;
          _pData = new Byte[_nCells];
          memset(_pData, 0, _nCells);
          return true;
        }
        void usePythonMemory(Byte* pData, const UInt nCells)
        {
          // delete a prior allocation
          if (_fMemoryAllocatedByPython == false  &&  _pData != NULL)
            delete [] _pData;

          // use the supplied memory and remember its size
          _nCells = nCells;
          _pData = pData;
          _fMemoryAllocatedByPython = true;
        }
        bool isSet(const UInt cellIdx) const
        {
          return _pData[cellIdx] != 0;
        }
        void set(const UInt cellIdx)
        {
          _pData[cellIdx] = 1;
        }
        void resetAll()
        {
          memset(_pData, 0, _nCells);
        }
        Byte* arrayPtr() const
        {
          // We expose the data array to Python.  For objects in derived
          // class CStateIndexed, a Python script can wreak havoc by
          // modifying the array, since the _cellsOn index will become
          // inconsistent.
          return _pData ;
        }
        void print(std::ostream& outStream) const
        {
          outStream << version() << " "
                    << _fMemoryAllocatedByPython << " "
                    << _nCells << std::endl;
          for (UInt i = 0; i < _nCells; ++i)
          {
            outStream << _pData[i] << " ";
          }
          outStream << std::endl
                    << "end" << std::endl;
        }
        void load(std::istream& inStream)
        {
          UInt version;
          inStream >> version;
          NTA_CHECK(version == 1);
          inStream >> _fMemoryAllocatedByPython
                   >> _nCells;
          for (UInt i = 0; i < _nCells; ++i)
          {
            inStream >> _pData[i];
          }
          std::string token;
          inStream >> token;
          NTA_CHECK(token == "end");
        }
        UInt version() const
        {
          return _version;
        }
      protected:
        UInt _version;
        UInt  _nCells;                      // should be static, since same size for all CStates
        Byte* _pData;                       // protected in C++, but exposed to the Python code
        bool  _fMemoryAllocatedByPython;
      };
      /**
       * Add an index to CState so that we can find all On cells without
       * a sequential search of the entire array.
       */
      class CStateIndexed : public CState
      {
      public:
        static const UInt VERSION = 1;

        CStateIndexed() : CState()
        {
          _version = VERSION;
          _countOn = 0;
          _isSorted = true;
        }
        CStateIndexed& operator=(CStateIndexed& o)
        {
          NTA_ASSERT(_nCells == o._nCells); // _nCells should be static, since it is the same size for all CStates
          // Is it faster to reset only the old nonzero indices and set only the new ones?
          std::vector<UInt>::iterator iterOn;
          // reset the old On cells
          for (iterOn = _cellsOn.begin(); iterOn != _cellsOn.end(); ++iterOn)
            _pData[*iterOn] = 0;
          // set the new On cells
          for (iterOn = o._cellsOn.begin(); iterOn != o._cellsOn.end(); ++iterOn)
            _pData[*iterOn] = 1;
          // use the new On tracker
          _cellsOn = o._cellsOn;
          _countOn = o._countOn;
          _isSorted = o._isSorted;
          return *this;
        }
        std::vector<UInt> cellsOn(bool fSorted = false)
        {
          // It's better for the caller to ask us to sort, rather than
          // to sort himself, since we can optimize out the sort when we
          // know the vector is already sorted.
          if (fSorted  &&  !_isSorted) {
            std::sort(_cellsOn.begin(), _cellsOn.end());
            _isSorted = true;
          }
          return _cellsOn;                  // returns a copy that can be modified
        }
        void set(const UInt cellIdx)
        {
          if (!isSet(cellIdx)) {
            CState::set(cellIdx);           // call the base class function
            if (_isSorted  &&  _countOn > 0  &&  cellIdx < _cellsOn.back())
              _isSorted = false;
            _cellsOn.push_back(cellIdx);    // add to the list of On cells
            _countOn++;                     // count the On cell; more efficient than .size()?
          }
        }
        void resetAll()
        {
          // Is it faster just to zero the _cellsOn indices?
          std::vector<UInt>::iterator iterOn;
          // reset the old On cells
          for (iterOn = _cellsOn.begin(); iterOn != _cellsOn.end(); ++iterOn)
            _pData[*iterOn] = 0;
          _cellsOn.clear();
          _countOn = 0;
          _isSorted = true;
        }
        void print(std::ostream& outStream) const
        {
          outStream << version() << " "
                    << _fMemoryAllocatedByPython << " "
                    << _nCells << std::endl;
          for (UInt i = 0; i < _nCells; ++i)
          {
            outStream << _pData[i] << " ";
          }
          outStream << _countOn << " ";
          outStream << _cellsOn.size() << " ";
          for (UInt i = 0; i < _cellsOn.size(); ++i)
          {
            outStream << _cellsOn[i] << " ";
          }
          outStream << "end" << std::endl;
        }
        void load(std::istream& inStream)
        {
          UInt version;
          inStream >> version;
          NTA_CHECK(version == 1);
          inStream >> _fMemoryAllocatedByPython
                   >> _nCells;
          for (UInt i = 0; i < _nCells; ++i)
          {
            inStream >> _pData[i];
          }
          inStream >> _countOn;
          UInt nCellsOn;
          inStream >> nCellsOn;
          UInt v;
          for (UInt i = 0; i < nCellsOn; ++i)
          {
            inStream >> v;
            _cellsOn.push_back(v);
          }
          std::string token;
          inStream >> token;
          NTA_CHECK(token == "end");
        }
        UInt version() const
        {
          return _version;
        }
      private:
        UInt _version;
        std::vector<UInt> _cellsOn;
        UInt _countOn;                      // how many cells are On
        bool _isSorted;                     // avoid unnecessary sorting
      };

      // These are iteration count tiers used when computing segment duty cycle
      const UInt _numTiers = 9;
      const UInt _dutyCycleTiers[] = {0,     100,   320,   1000,
                                      3200, 10000, 32000, 100000,
                                      320000};

      // This is the alpha used in each tier. dutyCycleAlphas[n] is used when
      /// iterationIdx > dutyCycleTiers[n]
      const Real _dutyCycleAlphas[]  = {0.0,     0.0032,   0.0010,   0.00032,
                                        0.00010, 0.000032, 0.000010, 0.0000032,
                                        0.0000010};

      //-----------------------------------------------------------------------
      // Forward declarations
      class Segment;


      //-----------------------------------------------------------------------
      struct InSynapseOrder
      {
        inline bool operator()(const InSynapse& a, const InSynapse& b) const
        {
          return a.srcCellIdx() < b.srcCellIdx();
        }
      };


      //-----------------------------------------------------------------------
      class Segment
      {
      public:
        typedef std::vector< InSynapse > InSynapses;

        // Variables representing various metrics of segment activity
        UInt _totalActivations;    // Total number of times segment was active
        UInt _positiveActivations; // Total number of times segment was
                                   // positively reinforced
        UInt _lastActiveIteration; // The last iteration on which the segment
                                   // became active (used in learning only)

        Real _lastPosDutyCycle;
        UInt _lastPosDutyCycleIteration;

      private:
        bool       _seqSegFlag;    // sequence segment flag
        InSynapses _synapses;      // incoming connections to this segment
        UInt       _nConnected;    // number of current connected synapses


      public:
        //----------------------------------------------------------------------
        inline Segment()
          : _totalActivations(1),
            _positiveActivations(1),
            _lastActiveIteration(0),
            _lastPosDutyCycle(0.0),
            _lastPosDutyCycleIteration(0),
            _seqSegFlag(false),
            _synapses(),
            _nConnected(0)
        {}

        //----------------------------------------------------------------------
        Segment(const InSynapses& _s, bool seqSegFlag,
                Real permConnected, UInt iteration);

        //-----------------------------------------------------------------------
        Segment(const Segment& o);

        //-----------------------------------------------------------------------
        Segment& operator=(const Segment& o);

        //-----------------------------------------------------------------------
        /**
          Checks that the synapses are unique and sorted in order of increasing
          src cell index. This is required by subsequent algorithms. Order
          matters for _removeSynapses and updateSynapses, but it prevents from
          partitioning the synapses in above/below permConnected, which test is
          the bottleneck in activity() (which is the overall bottleneck).

          TODO: Maybe we can remove the sorted restriction? Check if
          _removeSynapses and updateSynapses are major bottlenecks.

         */
        inline bool invariants() const
        {
          static std::vector<UInt> indices;
          static UInt highWaterSize = 0;
          if (highWaterSize < _synapses.size()) {
            highWaterSize = _synapses.size();
            indices.reserve(highWaterSize);
          }
          indices.clear();                  // purge residual data

          for (UInt i = 0; i != _synapses.size(); ++i)
            indices.push_back(_synapses[i].srcCellIdx());


#ifndef NDEBUG
          if (indices.size() != _synapses.size())
            std::cout << "Indices are not unique" << std::endl;

          if (!is_sorted(indices, true, true))
            std::cout << "Indices are not sorted" << std::endl;
#endif

          return is_sorted(indices, true, true);
        }

        //-----------------------------------------------------------------------
        /**
         * Check that _nConnected is equal to actual number of connected synapses
         *
         */
        inline bool checkConnected(Real permConnected) const {
          //
          UInt nc = 0;
          for (UInt i = 0; i != _synapses.size(); ++i)
            nc += (_synapses[i].permanence() >= permConnected);

          if (nc != _nConnected) {
            std::cout << "\nConnected stats inconsistent. _nConnected="
                      << _nConnected << ", computed nc=" << nc << std::endl;
          }

          return nc == _nConnected;
        }

        //----------------------------------------------------------------------
        /**
         * Various accessors
         */
        inline bool empty() const { return _synapses.empty(); }
        inline UInt size() const { return _synapses.size(); }
        inline bool isSequenceSegment() const { return _seqSegFlag; }
        inline UInt nConnected() const { return _nConnected; }
        inline UInt getTotalActivations() const { return _totalActivations;}
        inline UInt getPositiveActivations() const { return _positiveActivations;}
        inline UInt getLastActiveIteration() const { return _lastActiveIteration;}
        inline Real getLastPosDutyCycle() const    { return _lastPosDutyCycle;}
        inline UInt getLastPosDutyCycleIteration() const
                    { return _lastPosDutyCycleIteration;}

        //-----------------------------------------------------------------------
        /**
         * Checks whether the given src cellIdx is already contained in this segment
         * or not.
         * TODO: optimize with at least a binary search
         */
        inline bool has(UInt srcCellIdx) const
        {
          NTA_ASSERT(srcCellIdx != (UInt) -1);

          UInt lo = 0;
          UInt hi = _synapses.size();
          while (lo < hi) {
            const UInt test = (lo + hi)/2;
            if (_synapses[test].srcCellIdx() < srcCellIdx)
              lo = test + 1;
            else if (_synapses[test].srcCellIdx() > srcCellIdx)
              hi = test;
            else
              return true;
          }
          return false;
        }

        //-----------------------------------------------------------------------
        /**
         * Returns the permanence of the idx-th synapse on this Segment. That idx is *not*
         * a cell index, but just the index of the synapse on that segment, i.e. that
         * index will change if synapses are deleted from this segment in synpase
         * adaptation or global decay.
         */
        inline void setPermanence(UInt idx, Real val)
        {
          NTA_ASSERT(idx < _synapses.size());

          _synapses[idx].permanence() = val;
        }

        //-----------------------------------------------------------------------
        /**
         * Returns the permanence of the idx-th synapse on this Segment as a value
         */
        inline Real getPermanence(UInt idx) const
        {
          NTA_ASSERT(idx < _synapses.size());
          NTA_ASSERT(0 <= _synapses[idx].permanence());

          return _synapses[idx].permanence();
        }

        //-----------------------------------------------------------------------
        /**
         * Returns the source cell index of the synapse at index idx.
         */
        inline UInt getSrcCellIdx(UInt idx) const
        {
          NTA_ASSERT(idx < _synapses.size());
          return _synapses[idx].srcCellIdx();
        }

        //-----------------------------------------------------------------------
        /**
         * Returns the indices of all source cells in this segment.
         *
         * Parameter / return value:
         *   srcCells:      an empty vector. The indices will be returned in
         *                  this vector.
         */
        inline void getSrcCellIndices(std::vector<UInt>& srcCells) const
        {
          NTA_ASSERT(srcCells.size() == 0);
          for (UInt i= 0; i < _synapses.size(); i++) {
            srcCells.push_back(_synapses[i].srcCellIdx());
          }
        }

        //-----------------------------------------------------------------------
        /**
         * Note that _seqSegFlag is set back to zero when the synapses are erased: when
         * a segment is released, it's empty _AND_ it's no long a sequence segment.
         * This simplifies further tests in the algorithm.
         */
        inline void clear()
        {
          _synapses.clear();
          _synapses.resize(0);
          _seqSegFlag = false;
          _nConnected = 0;
        }

        //-----------------------------------------------------------------------
        inline const InSynapse& operator[](UInt idx) const
        {
          NTA_ASSERT(idx < size());
          return _synapses[idx];
        }

        //-----------------------------------------------------------------------
        /**
         * Adds synapses to this segment.
         *
         * Parameters:
         * ==========
         * - srcCells:        a collection of source cell indices (the sources of the
         *                    synapses). Source cell indices are unique on a segment,
         *                    and are kept in increasing order.
         * - initStrength:    the initial strength to set for the new synapses
         */
        void
        addSynapses(const std::set<UInt>& srcCells, Real initStrength,
                    Real permConnected);

        //-----------------------------------------------------------------------
        /**
         * Recompute _nConnected for this segment
         *
         * Parameters:
         * ==========
         * - permConnected: permanence values >= permConnected are considered
         *                  connected.
         *
         */
        void recomputeConnected(Real permConnected) {
          _nConnected = 0;
          for (UInt i = 0; i != _synapses.size(); ++i)
            if (_synapses[i].permanence() >= permConnected)
              ++ _nConnected;
        }

      private:

        //-----------------------------------------------------------------------
        /**
        A private method invoked by this Segment when synapses need to be
        removed. del contains the indices of the synapses to remove, as
        indices of synapses on this segment (not source cell indices). This
        method maintains the order of the synapses in the segment (they are
        sorted in order of increasing source cell index).
        */
        inline void _removeSynapses(const std::vector<UInt>& del)
        {
          // TODO: check what happens if synapses doesn't exist anymore
          // because of decay
          UInt i = 0, idel = 0, j = 0;

          while (i < _synapses.size() && idel < del.size()) {
            if (i == del[idel]) {
              ++i; ++idel;
            } else if (i < del[idel]) {
              _synapses[j++] = _synapses[i++];
            } else if (del[idel] < i) {
              NTA_CHECK(false); // Synapses have to be sorted!
            }
          }

          while (i < _synapses.size())
            _synapses[j++] = _synapses[i++];

          _synapses.resize(j);
        }

      public:
        //-----------------------------------------------------------------------
        /**
         * Updates synapses permanences, possibly removing synapses from the segment if their
         * permanence drops below 0.
         *
         * Parameters:
         * ==========
         * - synapses:       a collection of source cell indices to update (will be matched
         *                   with source cell index of each synapse)
         * - delta:          the amount to add to the permanence value of the updated
         *                   synapses
         * - removed:        collection of synapses that have been removed because their
         *                   permanence dropped below 0 (srcCellIdx of synapses).
         *
         * TODO: have synapses be 2 pointers, to avoid copies in adaptSegments
         */
        template <typename T2> // this blocks swig wrapping which doesn't happen right
        inline void
        updateSynapses(const std::vector<T2>& synapses, Real delta,
                       Real permMax, Real permConnected,
                       std::vector<T2>& removed)
        {
          {
            NTA_ASSERT(invariants());
            NTA_ASSERT(is_sorted(synapses));
          }

          std::vector<UInt> del;

          UInt i1 = 0, i2 = 0;

          while (i1 < size() && i2 < synapses.size()) {

            if (_synapses[i1].srcCellIdx() == synapses[i2]) {

              Real oldPerm = getPermanence(i1);
              Real newPerm = std::min(oldPerm + delta, permMax);

              if (newPerm <= 0) {
                removed.push_back(_synapses[i1].srcCellIdx());
                del.push_back(i1);
              }

              setPermanence(i1, newPerm);

              int wasConnected = (int) (oldPerm >= permConnected);
              int isConnected = (int) (newPerm >= permConnected);

              _nConnected += isConnected - wasConnected;

              ++i1; ++i2;

            } else if (_synapses[i1].srcCellIdx() < synapses[i2]) {
              ++i1;
            } else {
              ++i2;
            }
          }

          // _removeSynapses maintains the order of the synapses
          _removeSynapses(del);

          NTA_ASSERT(invariants());
        }

        //----------------------------------------------------------------------
        /**
         * Subtract decay from each synapses' permanence value.
         * Synapses whose permanence drops below 0 are removed and their source
         * indices are inserted into the "removed" list.
         *
         * Parameters:
         * ==========
         * - decay:       the amount to subtract from the permanence value the
         *                synapses
         * - removed:     srcCellIdx of the synapses that are removed
         */
        void decaySynapses2(Real decay, std::vector<UInt>& removed,
                            Real permConnected);

        //----------------------------------------------------------------------
        /**
         * Decay synapses' permanence value. Synapses whose permanence drops
         * below 0 are removed.
         *
         * Parameters:
         * ==========
         * - decay:       the amount to subtract from the permanence value the
         *                synapses
         * - removed:     srcCellIdx of the synapses that are removed
         */
        void decaySynapses(Real decay, std::vector<UInt>& removed,
                           Real permConnected, bool doDecay=true);

        //----------------------------------------------------------------------
        /**
         * Free up some synapses in this segment. We always free up inactive
         * synapses (lowest permanence freed up first) before we start to free
         * up active ones.
         *
         * Parameters:
         * ==========
         * numToFree:                 num synapses we have to remove
         * inactiveSynapseIndices:    list of inactive synapses (src cell indices)
         * inactiveSegmentIndices:    list of inactive synapses (index within segment)
         * activeSynapseIndices:      list of active synapses (src cell indices)
         * activeSegmentIndices:      list of active synapses (index within segment)
         * removed:                   srcCellIdx of the synapses that are
         *                            removed
         * verbosity:                 verbosity level for debug printing
         * nCellsPerCol:              number of cells per column (for debug
         *                            printing)
         * permMax:                   maximum allowed permanence value
         */
        void freeNSynapses(UInt numToFree,
                           std::vector<UInt> &inactiveSynapseIndices,
                           std::vector<UInt> &inactiveSegmentIndices,
                           std::vector<UInt> &activeSynapseIndices,
                           std::vector<UInt> &activeSegmentIndices,
                           std::vector<UInt>& removed, UInt verbosity,
                           UInt nCellsPerCol, Real permMax);

        //----------------------------------------------------------------------
        /**
         * Computes the activity level for a segment given permConnected and
         * activationThreshold. A segment is active if it has more than
         * activationThreshold connected synapses that are active due to
         * activeState.
         *
         * Parameters:
         * ==========
         * - activities: pointer to activeStateT or activeStateT1
         *
         * NOTE: called getSegmentActivityLevel in Python
         */
        bool isActive(const CState& activities,
                      Real permConnected, UInt activationThreshold) const;

        //----------------------------------------------------------------------
        /**
         * Compute the activity level of a segment using cell activity levels
         * contain in activities.
         *
         * Parameters:
         * ==========
         * - activities: pointer to an array of cell activities.
         *
         * - permConnected: permanence values >= permConnected are considered
         *                  connected.
         *
         * - connectedSynapsesOnly: if true, only consider synapses that are
         *                          connected.
         */
        UInt computeActivity(const CState& activities, Real permConnected,
                                         bool connectedSynapsesOnly) const;

        //----------------------------------------------------------------------
        /**
         * Compute/update and return the positive activations duty cycle of
         * this segment. This is a measure of how often this segment is
         * providing good predictions.
         *
         * Parameters:
         * ==========
         * iteration:   Current compute iteration. Must be > 0!
         * active:      True if segment just provided a good prediction
         *
         */
        Real dutyCycle(UInt iteration, bool active, bool readOnly);


        //----------------------------------------------------------------------
        /**
         * Returns true if iteration is equal to one of the duty cycle tiers.
         */
        static bool atDutyCycleTier(UInt iteration)
        {
          for (UInt i= 0; i < _numTiers; i++) {
            if (iteration == _dutyCycleTiers[i]) return true;
          }
          return false;
        }

        //----------------------------------------------------------------------
        // PERSISTENCE
        //----------------------------------------------------------------------
        inline UInt persistentSize() const
        {
          std::stringstream buff;
          this->save(buff);
          return buff.str().size();
        }

        //----------------------------------------------------------------------
        inline void save(std::ostream& outStream) const
        {
          NTA_ASSERT(invariants());
          outStream << size() << ' '
                    << _seqSegFlag << ' '
                    << _nConnected << ' '
                    << _totalActivations << ' '
                    << _positiveActivations << ' '
                    << _lastActiveIteration << ' '
                    << _lastPosDutyCycle << ' '
                    << _lastPosDutyCycleIteration << ' ';
          binary_save(outStream, _synapses);
          outStream << ' ';
        }

        //----------------------------------------------------------------------
        inline void load(std::istream& inStream)
        {
          UInt n = 0;
          inStream >> n
                   >> _seqSegFlag
                   >> _nConnected
                   >> _totalActivations
                   >> _positiveActivations
                   >> _lastActiveIteration
                   >> _lastPosDutyCycle
                   >> _lastPosDutyCycleIteration;
          _synapses.resize(n);
          inStream.ignore(1);
          binary_load(inStream, _synapses);
          NTA_ASSERT(invariants());
        }

        //-----------------------------------------------------------------------
        /**
         * Print the segment in a human readable form. If nCellsPerCol is specified
         * then the source col/cell for each synapse will be printed instead of
         * cell index.
         */
        void print(std::ostream& outStream, UInt nCellsPerCol = 0) const;
      };

      //-----------------------------------------------------------------------
#ifndef SWIG
      std::ostream& operator<<(std::ostream& outStream, const Segment& seg);
      std::ostream& operator<<(std::ostream& outStream, const CState& cstate);
      std::ostream& operator<<(std::ostream& outStream,
                               const CStateIndexed& cstate);
#endif

      //-----------------------------------------------------------------------
    } // end namespace Cells4
  } // end namespace algorithms
} // end namespace nta

  //-----------------------------------------------------------------------
#endif // NTA_SEGMENT_HPP
