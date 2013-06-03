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

#ifndef NTA_CELLS_2_HPP
#define NTA_CELLS_2_HPP

#include <nta/math/array_algo.hpp>

/*
#include <sys/time.h>
#include <sys/types.h>
#include <sys/syscall.h>

//--------------------------------------------------------------------------------
struct Timer
{
  struct timeval t0, t1;
  
  inline Timer() { gettimeofday(&t0, NULL); }
  inline void start() { gettimeofday(&t0, NULL); }
  inline void restart() { gettimeofday(&t0, NULL); }
  inline double elapsed() 
  {
    gettimeofday(&t1, NULL);
    return t1.tv_sec+1e-6*t1.tv_usec - (t0.tv_sec+1e-6*t0.tv_usec);
  }
};
*/

//--------------------------------------------------------------------------------

namespace nta {
  namespace algorithms {
    namespace Cells2 {

      // Forward declarations
      template <typename U, typename I, typename T>
      struct Point;

      template <typename U, typename I, typename T>
      struct Delta;

      template <typename U, typename I, typename T>
      struct Synapse;

      template <typename U, typename I, typename T>
      struct OutSynapse;

      template <typename U, typename I, typename T>
      class Segment;

      template <typename U, typename I, typename T>
      class Branch;

      template <typename U, typename I, typename T>
      class Cells;

      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct Point
      {
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

//xxx        typedef Cells<U,I,T> Cells;

        diff_type row, col;
        
        inline Point(size_type idx, const Cells<U,I,T>* cells =NULL)
          : row(idx / cells->cellsWidth()),
            col(idx % cells->cellsWidth())
        {}
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct Delta
      {
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

//xxx        typedef Point<U,I,T> Point;
//xxx        typedef Cells<U,I,T> Cells;

        diff_type d_row, d_col;
        
        inline Delta(const Point<U,I,T>& a, const Point<U,I,T>& b, const Cells<U,I,T>* cells =NULL)
          : d_row(a.row - b.row), d_col(a.col - b.col) {}
      };

      template <typename U, typename I, typename T>
      inline Delta<U,I,T> operator-(const Point<U,I,T>& a, const Point<U,I,T>& b)
      {
        return Delta<U,I,T>(a.row - b.row, a.col - b.col);
      }

      template <typename U, typename I, typename T>
      inline Point<U,I,T> operator+(const Point<U,I,T>& a, const Delta<U,I,T>& d)
      {
        return Point<U,I,T>(a.row + d.d_row, a.col + d.d_col);
      }

      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct Synapse
      {
        // TODO: make I (signed) short
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

//xxx        typedef Cells<U,I,T> Cells;

        // TODO: unaligned on 4 bytes? 6 bytes + 4... 
        diff_type src_master; //, dst_master;
        diff_type d_row, d_col;
        value_type strength;

        // The null synapse (can be a null key in sparsehash)
        inline Synapse()
          : src_master(-1),
            d_row(0), d_col(0),
            strength(0)
        {}

        inline Synapse(diff_type src, diff_type dst, 
                       diff_type dr, diff_type dc,
                       value_type s, const Cells<U,I,T>* cells =NULL)
          : src_master(src), //dst_master(dst),
            d_row(dr), d_col(dc),
            strength(s)
        {
          NTA_ASSERT(check_invariants(cells));
        }

        inline Synapse(const Synapse& o)
          : src_master(o.src_master), //dst_master(o.dst_master),
            d_row(o.d_row), d_col(o.d_col),
            strength(o.strength)
        {}

        inline Synapse& operator=(const Synapse& o)
        {
          if (&o != this) {
            src_master = o.src_master;
            //dst_master = o.dst_master;
            d_row = o.d_row;
            d_col = o.d_col;
            strength = o.strength;
          }
          return *this;
        }

        /**
         * We always have d_row != 0 || d_col != 0:
         * - the src and dst masters are different, at least one of d_row,d_col
         *   will be != 0 by construction
         * - the src and dst masters are the same, that is possible,
         *   but at least one of d_row,d_col needs to be != 0, otherwise
         *   we would have a synapse between a cell and itself. 
         */
        inline bool check_invariants(const Cells<U,I,T>* cells =NULL) const
        {
          bool b1 = true //(src_master != dst_master)
            && (d_row != 0 || d_col != 0)
            && (0 <= strength);

          if (cells) {
            b1 &= (src_master < (diff_type) cells->nMasters()); 
            //&& dst_master < (diff_type) cells->nMasters());
            b1 &= (abs(d_row) <= (diff_type) cells->learnRadius() 
                   && abs(d_col) <= (diff_type) cells->learnRadius());
          }

          if (!b1) {
            std::cout << "Incorrect in synapse:",
              *this, std::endl;
            if (cells)
              std::cout << "learn radius=", cells->learnRadius(), std::endl;
          }

          return b1;
        }

        inline size_type n_bytes() const 
        {
          return sizeof(size_type) + 4 * sizeof(diff_type) + sizeof(value_type);
        }

        inline std::pair<diff_type, diff_type> delta() const 
        {
          return std::make_pair(d_row, d_col);
        }

        inline std::pair<diff_type, diff_type> neg_delta() const
        {
          return std::make_pair(-d_row, -d_col);
        }

        inline void print(std::ostream& out_stream) const 
        {
          out_stream << src_master //"->" << dst_master
                     << " " << d_row << "," << d_col << " (" << strength << ")";
        }

        inline bool equals(const Synapse& o) const
        {
          // For unicity on a segment, only the d_row, d_col need to be compared,
          // because the same displacements imply the same masters.
          return //src_master == o.src_master 
            //&& dst_master == o.dst_master
            d_row == o.d_row && d_col == o.d_col;
        }

        inline bool lt(const Synapse& o) const
        {
          if (d_row < o.d_row)
            return true;
          else if (d_row == o.d_row)
            return d_col < o.d_col;
          return false;
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct hash_synapse
      {
        inline size_t operator()(const Synapse<U,I,T>& s) const
        {
          return s.d_row * 1000 + s.d_col;
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      inline std::ostream& operator<<(std::ostream& out_stream, const Synapse<U,I,T>& s)
      {
        s.print(out_stream);
        return out_stream;
      }

      template <typename U, typename I, typename T>
      inline bool operator==(const Synapse<U,I,T>& a, const Synapse<U,I,T>& b)
      {
        return a.equals(b);
      }

      template <typename U, typename I, typename T>
      inline bool operator<(const Synapse<U,I,T>& a, const Synapse<U,I,T>& b)
      {
        return a.lt(b);
      }

      template <typename U, typename I, typename T>
      struct lt_out_seg
      {
        inline bool operator()(const Synapse<U,I,T>& a, const Synapse<U,I,T>& b) const
        {
          return a < b;
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct OutSynapse
      {
        // TODO: point to counterpart and don't store deltas?
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

//xxx        typedef Cells<U,I,T> Cells;

        size_type dst_seg;
        diff_type d_row, d_col;
  
        inline OutSynapse(size_type s =0, diff_type dr =0, diff_type dc =0, 
                          const Cells<U,I,T>* cells =NULL)
          : dst_seg(s), d_row(dr), d_col(dc)
        {
          NTA_ASSERT(check_invariants(cells));
        }
  
        inline OutSynapse(const OutSynapse& o)
          : dst_seg(o.dst_seg), d_row(o.d_row), d_col(o.d_col)
        {}
  
        inline OutSynapse& operator=(const OutSynapse& o)
        {
          dst_seg = o.dst_seg;
          d_row = o.d_row;
          d_col = o.d_col;
          return *this;
        }

        inline bool check_invariants(const Cells<U,I,T>* cells =NULL) const
        {
          bool b1 = 0 <= dst_seg && (d_row != 0 || d_col != 0);

          if (cells) 
            b1 &= abs(d_row) <= (diff_type) cells->learnRadius()
              && abs(d_col) <= (diff_type) cells->learnRadius();

          if (!b1) {
            std::cout << "Incorrect out synapse:",
              *this, std::endl;
            if (cells)
              std::cout << "learning radius=", cells->learnRadius(), std::endl;
            throw;
          }

          return b1;
        }

        inline size_type n_bytes() const 
        { 
          return sizeof(size_type) + 2*sizeof(diff_type); 
        }

        inline std::pair<diff_type, diff_type> delta() const 
        {
          return std::make_pair(d_row, d_col);
        }

        inline std::pair<diff_type, diff_type> neg_delta() const
        {
          return std::make_pair(-d_row, -d_col);
        }

        inline void print(std::ostream& out_stream) const 
        {
          out_stream << dst_seg << " " << d_row << "," << d_col;
        }

        // Outgoings are unique from a source to a dest master when taking 
        // into account the seg id,
        // i.e. we allow outgoings from a cell to two or more different
        // segs of another cell (not the same seg though).
        inline bool equals(const OutSynapse& o) const
        {
          return dst_seg == o.dst_seg && d_row == o.d_row && d_col == o.d_col;
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      inline std::ostream& operator<<(std::ostream& out_stream, 
                                      const OutSynapse<U,I,T>& o)
      {
        o.print(out_stream);
        return out_stream;
      }

      template <typename U, typename I, typename T>
      inline bool operator==(const OutSynapse<U,I,T>& o1, const OutSynapse<U,I,T>& o2)
      {
        return o1.equals(o2);
      }

      //--------------------------------------------------------------------------------
      template <typename S1, typename S2>
      inline bool reciprocal(const S1& s1, const S2& s2) 
      {
        return s1.d_row == - s2.d_row && s1.d_col == - s2.d_col;
      }

      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      class Segment
      {
      public:
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

//xxx        typedef Synapse<U,I,T> Synapse;
        typedef typename std::vector< Synapse<U,I,T> > Synapses;  
//xxx        typedef Cells<U,I,T> Cells;

      private:

        Synapses synapses;

      public:

        //--------------------------------------------------------------------------------
        inline 
        Segment() //const Synapses& s =Synapses())
          : synapses()
        {
          //sort(*this); //ut
        }

        //--------------------------------------------------------------------------------
        inline bool empty() const { return synapses.empty(); }
        inline size_type size() const { return synapses.size(); }
        inline Synapse<U,I,T>& operator[](size_type i) { return synapses[i]; }
        inline const Synapse<U,I,T>& operator[](size_type i) const { return synapses[i]; }
        inline void resize(size_type n) { synapses.resize(n); }

        //--------------------------------------------------------------------------------
        /**
         * Returns the exact number of bytes taken up by this segment.
         */
        inline size_t n_bytes() const 
        { 
          Synapse<U,I,T> a[2];
          return synapses.size() * (&a[1] - &a[0]);
        }

        //--------------------------------------------------------------------------------
        inline size_type nSynapsesAboveThreshold(value_type threshold =0) const 
        {
          if (threshold <= 0)
            return synapses.size();
    
          size_type n = 0;
    
          for (size_type i = 0; i != synapses.size(); ++i)
            if (synapses[i].strength > threshold)
              ++n;

          return n;
        }

        //--------------------------------------------------------------------------------
        inline void 
        addSynapses(size_type dst, 
                    const std::vector<diff_type>& src_deltas, 
                    value_type init_strength,
                    Cells<U,I,T>* cells =NULL)
        {
          {
            NTA_ASSERT(0 < src_deltas.size());
            NTA_ASSERT(0 < init_strength);
          }

          // TODO: store dst only once, for the whole segment?
          // Watch out for arg eval order in call: *deltas++, *deltas++ inverts
          // the values!!!
          const diff_type* p = &src_deltas[0], *p_end = p + src_deltas.size();

          while (p != p_end) {
            diff_type src = *p++;
            diff_type drow = *p++;
            diff_type dcol = *p++;
            Synapse<U,I,T> s(src, dst, drow, dcol, init_strength, cells);
            NTA_ASSERT(not_in(s, synapses)); // check unicity
            synapses.push_back(s);
          }
    
          //sort(*this); //ut
        }

        //--------------------------------------------------------------------------------
        inline void removeSynapse(size_type syn_idx)
        {
          NTA_ASSERT(syn_idx < synapses.size());

          // TODO: CHANGE THAT, so that addresses stay constant,
          // and we can use pointers (in hashes, for example)
          // changes the order of the synapses!!!
          std::swap(synapses[syn_idx], synapses.back());
          synapses.pop_back();
        }

        //--------------------------------------------------------------------------------
        // PERSISTENCE
        //--------------------------------------------------------------------------------

        //--------------------------------------------------------------------------------
        /**
         * Return the size of this segment when saved on a stream, in bytes.
         */
        inline size_type persistent_size() const
        {
          std::stringstream buff;
          this->save(buff);
          return buff.str().size();
        }

        //--------------------------------------------------------------------------------
        /**
         * Save this segment to a stream. Does a binary save for the synapses. Doesn't 
         * save the id or the Branch pointer. Those are set by Branch::create_segment.
         */
        inline void save(std::ostream& out_stream) const
        {
          out_stream << synapses.size() << ' ';
          /*nta::*/binary_save(out_stream, synapses);
          out_stream << ' ';
        }

        //--------------------------------------------------------------------------------
        /**
         * Load this segment from a stream.
         * 
         * Don't forget to initialize the axon projections here!
         */
        inline void load(std::istream& in_stream)
        {
          size_t n = 0;
          in_stream >> n;
          synapses.resize(n);
          in_stream.ignore(1);
          /*nta::*/binary_load(in_stream, synapses);
        }

        //--------------------------------------------------------------------------------
        inline void print(std::ostream& out_stream) const
        {
          if (!synapses.empty())
            for (size_type i = 0; i != synapses.size(); ++i) {
              out_stream << synapses[i];
              if (i < synapses.size() - 1) // !synapses.empty
                out_stream << " | ";
            }
          else
            out_stream << "empty segment";
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      inline std::ostream& operator<<(std::ostream& out_stream, const Segment<U,I,T>& x)
      {
        x.print(out_stream);
        return out_stream;
      }

      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      // BRANCH
      //--------------------------------------------------------------------------------
      /**
       * A Branch is a component of a dendritic tree. A branch has segments that contain
       * synapses, and children branches. It also has a parent Branch, or it is a root
       * of the dendritic tree it belongs to.
       *
       * A Branch always has at least one segment. The algorithms rely on this when 
       * computing activations. The Branch constructors don't create that mandatory 
       * initial segment for you though. Also, you need to be careful when you remove 
       * segments, that you leave at least one on the branch. Finally, cut_at_segment 
       * will remove a whole sub_tree if you call it with index 0 (that would be like 
       * removing all the segments on the branch, therefore the branch itself is removed, 
       * and all its children).
       */
      template <typename U, typename I, typename T>
      class Branch
      {
      public:
        typedef U size_type;
        typedef I diff_type;
        typedef T value_type;

        typedef typename Segment<U,I,T>::Synapses Synapses;
//xxx        typedef Segment<U,I,T> Segment;
//xxx        typedef Cells<U,I,T> Cells;

        //private:
        //Cells*                  _cells;      
        //size_type               _cell_idx;
        // TODO: keep a single vector with a position after which the segments are free:
        // the index of the segments can change
        // TODO: change from pointers to instances?
        std::vector< Segment<U,I,T> >    _segments;
        std::vector<size_type>  _free_segments;

      public:
        //--------------------------------------------------------------------------------
        inline 
        Branch() //Cells* c =NULL) //, size_type cell_idx =0)
          : //_cells(c),
          //_cell_idx(cell_idx),
          _segments(0),
          _free_segments(0)
        {}
      
        //--------------------------------------------------------------------------------
        inline ~Branch()
        {
          _segments.resize(0);
          _free_segments.resize(0); // TODO: reuse free segments?
        }

        //--------------------------------------------------------------------------------
        //inline Cells* cells() const { NTA_ASSERT(_cells); return _cells; }
        //inline size_type cell_index() const { return _cell_idx; }
  
        //--------------------------------------------------------------------------------
        // TODO: watch out, can return free'd segment (will be empty)!!!!
        inline Segment<U,I,T>& operator[](size_type idx) 
        {
          NTA_ASSERT(0 <= idx && idx < _segments.size());
          NTA_ASSERT(not_in(idx, _free_segments) || _segments[idx].empty());

          return _segments[idx];
        }

        //--------------------------------------------------------------------------------
        inline const Segment<U,I,T>& operator[](size_type idx) const 
        {
          NTA_ASSERT(0 <= idx && idx < _segments.size());
          NTA_ASSERT(not_in(idx, _free_segments) || _segments[idx].empty());

          return _segments[idx];
        }
  
        //--------------------------------------------------------------------------------
        inline std::vector< Segment<U,I,T> >& getAllSegments()
        {
          return _segments;
        }

        //--------------------------------------------------------------------------------
        inline size_type nAllocatedSegments() const 
        {
          return _segments.size();
        }
  
        //--------------------------------------------------------------------------------
        inline size_type nActiveSegments() const 
        { 
          return _segments.size() - _free_segments.size(); 
        }

        //--------------------------------------------------------------------------------
        inline size_type nSynapsesAboveThreshold(value_type threshold =0) const
        {
          size_type n = 0;
          for (size_type i = 0; i != _segments.size(); ++i)
            n += _segments[i].nSynapsesAboveThreshold(threshold);
          return n;
        }

        //--------------------------------------------------------------------------------
        inline size_type nSynapsesMax() const
        {
          size_type n = 0;
          for (size_type i = 0; i != _segments.size(); ++i)
            n = std::max(n, (size_type) _segments[i].size());
          return n;
        }

        //--------------------------------------------------------------------------------
        inline bool isActiveSegment(size_type idx) const
        {
          NTA_ASSERT(idx < _segments.size());
          return not_in(idx, _free_segments);
        }

        //--------------------------------------------------------------------------------
        inline bool empty() const { return _segments.size() == _free_segments.size(); }

        //--------------------------------------------------------------------------------
        // TODO: can break this, as long as the segment indices are consistent
        // with update. Python doesn't change or directly accesses segments based on 
        // the segment indices.
        inline size_type getFreeSegment()
        {
          size_type seg_idx = 0;

          if (_free_segments.empty()) {
            seg_idx = _segments.size();
            _segments.resize(_segments.size() + 1);
          } else {
            seg_idx = _free_segments.back();
            _free_segments.pop_back();
          }

          NTA_ASSERT(seg_idx < _segments.size());
          NTA_ASSERT(not_in(seg_idx, _free_segments));
          NTA_ASSERT(_segments[seg_idx].empty()); // important in case we push_back 

          return seg_idx;
        }

        //--------------------------------------------------------------------------------
        inline void releaseSegment(size_type seg_idx)
        {
          NTA_ASSERT(seg_idx < _segments.size());
          NTA_ASSERT(not_in(seg_idx, _free_segments));

          _segments[seg_idx].resize(0); // important in case we push_back later
          _free_segments.push_back(seg_idx);

          NTA_ASSERT(_segments[seg_idx].empty());
        }

        //--------------------------------------------------------------------------------
        inline std::vector<size_type> getActiveSegmentIndices() const
        {
          std::vector<size_type> s;
          for (size_type i = 0; i != _segments.size(); ++i)
            if (!_segments[i].empty())
              s.push_back(i);
          return s;
        }

        //--------------------------------------------------------------------------------
        // PERSISTENCE
        //--------------------------------------------------------------------------------
        inline size_type persistent_size() const
        {
          std::stringstream buff;
          this->save(buff);
          return buff.str().size();
        }

        //--------------------------------------------------------------------------------
        inline void save(std::ostream& out_stream) const
        {
          out_stream << _segments.size() << ' ';
          for (size_type i = 0; i != _segments.size(); ++i) {
            //if (!_segments[i].empty()) {
            _segments[i].save(out_stream);
            out_stream << ' ';
            //}
          }
        }

        //--------------------------------------------------------------------------------
        inline void load(std::istream& in_stream) 
        {
          int n = 0;
    
          in_stream >> n;
          NTA_ASSERT(0 <= n);

          _segments.resize(n);
          _free_segments.resize(0);
    
          for (size_type i = 0; i != (size_type) n; ++i) {
            _segments[i].load(in_stream);
            if (_segments[i].empty())
              _free_segments.push_back(i);
          }
        }

        //--------------------------------------------------------------------------------
        inline void print(std::ostream& out_stream) const
        {
          out_stream << nActiveSegments() << "/" << nAllocatedSegments() << ": ";
          for (size_type i = 0; i != _segments.size(); ++i) 
            if (!_segments[i].empty())
              out_stream << "[" << _segments[i] << "]";
        }
      };

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      inline std::ostream& operator<<(std::ostream& out_stream, const Branch<U,I,T>& b)
      {
        b.print(out_stream);
        return out_stream;
      }

      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      struct master_delta 
      {
        typedef U size_type;
        typedef I diff_type;
        typedef int long_diff_type;
        typedef T value_type;

//xxx        typedef OutSynapse<U,I,T> OutSynapse;
        typedef std::vector< OutSynapse<U,I,T> > OutSynapses;

        OutSynapses new_synapses;
        OutSynapses del_synapses;
        
        inline void clear() 
        {
          new_synapses.clear();
          del_synapses.clear();
        }

        inline bool empty() const 
        { 
          return new_synapses.empty() && del_synapses.empty(); 
        }

        inline void add_new(const OutSynapse<U,I,T>& out_synapse)
        {
          NTA_ASSERT(out_synapse.check_invariants());

          new_synapses.push_back(out_synapse);
        }

        inline void add_del(const OutSynapse<U,I,T>& out_synapse)
        {
          NTA_ASSERT(out_synapse.check_invariants());

          del_synapses.push_back(out_synapse);
        }
      };
      
      //--------------------------------------------------------------------------------
      // CELLS
      //--------------------------------------------------------------------------------
      template <typename U, typename I, typename T>
      class Cells
      {
      public:
        typedef U size_type;
        typedef I diff_type;
        typedef int long_diff_type;
        typedef T value_type;
  
//xxx        typedef Point<U,I,T> Point;
//xxx        typedef Delta<U,I,T> Delta;
//xxx        typedef Synapse<U,I,T> Synapse;
//xxx        typedef OutSynapse<U,I,T> OutSynapse;
//xxx        typedef Segment<U,I,T> Segment;
//xxx        typedef Branch<U,I,T> Branch;

        typedef enum { trace_update, 
                       trace_activation,
                       trace_propagation,
                       trace_add_synapses,
                       trace_delete_synapse,
                       cross_check_synapses,
                       capture_vectors,
                       show_stats_at_end } Debug;

      private:
        nta::Random rng;

        size_type n_cells, n_masters;
        size_type c_height, c_width;
        size_type clone_height, clone_width;

        size_type learn_radius;
        size_type learn_area;
        value_type syn_init_perm;
        value_type syn_min_perm;
        value_type syn_perm_orphan_dec;
        value_type syn_perm_match_inc;
        value_type syn_perm_mix_match_dec;
        size_type seg_empty_th;
        size_type max_n_segs_per_cell;

        std::vector<size_type> cl_map;
        std::vector<std::vector<size_type> > inv_cl_map;
        std::vector< Branch<U,I,T> > branches;

        typedef std::vector< OutSynapse<U,I,T> > OutSynapses;
        std::vector<OutSynapses> all_out_synapses;

        std::vector<int> cell_activity;
        std::vector<std::vector<short> > segment_activity;

        std::vector<size_type> bounds;
        std::vector<size_type> candidates;
        Indicator<size_type, unsigned short> existing_src;
        ByteVector dense_input;

        ByteVector activity, prev_activity;
        std::vector<size_type> prev_active;
        std::vector<master_delta<U,I,T> > master_deltas;

        struct CellCache
        {
          size_type max_seg_idx;
          size_type max_activity;

          std::vector<size_type> active_segs;
          std::vector<size_type> active_levels;
        };

        std::vector<CellCache> cache;
        size_type cached_threshold_for_best;
        size_type cached_threshold_for_active;
        std::vector<unsigned char> changed;

        ByteVector safe_cells;

        // Statistics
        unsigned long long n_iterations;
        unsigned long long n_instructions_processed;
        unsigned long long n_cells_active;
        unsigned long long n_segments_visited;
        unsigned long long n_synapses_visited;
        unsigned long long n_changed_cells;
        unsigned long long n_act_change_cells;
        unsigned long long n_checks;
        unsigned long long n_no_checks;
        unsigned long long n_cells_to_clear;
        unsigned long long n_segs_to_clear;
        unsigned long long n_modified_synapses;

        double deltas_time;
        double prop_time;
        double clear_time;
        double seg_prop_time;
        double cell_prop_time;
        double act_time;
        double update_time;
        double get_candidates_time;
        mutable double num_syn_time;
        mutable double abs_syn_time;
        mutable double offset_time;
        double densify_time;
        double insert_in_update_time;
        double delete_synapses_time;
        double add_synapses_time;
        double add_syn_time_in_update;
        double release_segment_time;
        double decay_time;

        // Debug
        std::set<Debug> debug_flags;

      public:

        //--------------------------------------------------------------------------------
        /**
         * Default constructor needed when lifting from persistence.
         */
        inline Cells(size_type cHeight =0, size_type cWidth =0, 
                     size_type cloneHeight =0, size_type cloneWidth =0,
                     size_type learningRadius =1,
                     int seed =-1,
                     value_type synInitPerm =10, value_type synMinPerm =1, 
                     value_type synPermOrphanDec =0, value_type synPermMatchInc =0,
                     value_type synPermMixAndMatchDec =0,
                     size_type segEmptyTh =0,
                     size_type maxNSegsPerCell =32) 
          : rng(seed == -1 ? rand() : seed),
            n_cells(cHeight * cWidth),
            n_masters(cloneHeight * cloneWidth),
            c_height(cHeight),
            c_width(cWidth),
            clone_height(cloneHeight),
            clone_width(cloneWidth),
            learn_radius(learningRadius),
            learn_area((2*learn_radius+1)*(2*learn_radius+1) - 1),
            syn_init_perm(synInitPerm),
            syn_min_perm(synMinPerm),
            syn_perm_orphan_dec(synPermOrphanDec),
            syn_perm_match_inc(synPermMatchInc),
            syn_perm_mix_match_dec(synPermMixAndMatchDec),
            seg_empty_th(segEmptyTh),
            max_n_segs_per_cell(maxNSegsPerCell)
        {
          // members we persist
          branches.resize(n_masters);
          all_out_synapses.resize(n_masters);

          // members we don't persist
          finish_init();
        }

        //--------------------------------------------------------------------------------
        // members we don't persist
        void finish_init()
        {
          cell_activity.resize(n_cells);

          segment_activity.resize(n_cells);
          for (size_type i = 0; i != n_cells; ++i)
            segment_activity[i].resize(max_n_segs_per_cell);

          candidates.reserve(n_cells);
          existing_src.resize(n_cells); 
          dense_input.resize(n_cells);

          // Initialize array of "safe" cells
          safe_cells.resize(n_cells, 0);

          for (size_type row = 0; row != c_height; ++row)
            for (size_type col = 0; col != c_width; ++col)
              if (learn_radius < row && row < c_height - learn_radius
                  && learn_radius < col && col < c_width - learn_radius)
                safe_cells[row*c_width+col] = 1;

          activity.resize(n_cells, 0);
          prev_activity.resize(n_cells, 0);
          master_deltas.resize(n_masters);
          cache.resize(n_cells);
          cached_threshold_for_best = std::numeric_limits<size_type>::max();
          cached_threshold_for_active = std::numeric_limits<size_type>::max();
          changed.resize(n_cells, 1);

          init_cl_maps();
          init_bounds();
          init_stats();
        }

        //--------------------------------------------------------------------------------
        void init_stats()
        {
          n_iterations = 0;
          n_instructions_processed = 0;
          n_cells_active = 0;
          n_segments_visited = 0;
          n_synapses_visited = 0;
          n_changed_cells = 0;
          n_act_change_cells = 0;
          n_checks = 0;
          n_no_checks = 0;
          n_cells_to_clear = 0;
          n_segs_to_clear = 0;
          n_modified_synapses = 0;

          deltas_time = 0;
          prop_time = 0;
          clear_time = 0;
          seg_prop_time = 0;
          cell_prop_time = 0;
          act_time = 0;
          update_time = 0;
          get_candidates_time = 0;
          num_syn_time = 0;
          abs_syn_time = 0;
          offset_time = 0;
          densify_time = 0;
          insert_in_update_time = 0;
          delete_synapses_time = 0;
          add_synapses_time = 0;
          add_syn_time_in_update = 0;
          release_segment_time = 0;
          decay_time = 0;
        }

        //--------------------------------------------------------------------------------
        ~Cells()
        {
          //if (is_in(show_stats_at_end, debug_flags))
          //print_stats();
        }

      private:
        //--------------------------------------------------------------------------------
        inline void init_cl_maps()
        {
          cl_map.resize(n_cells);
          inv_cl_map.resize(n_masters);
    
          for (size_type i = 0; i != n_cells; ++i) {
            cl_map[i] = clone_width * ((i / c_width) % clone_height) 
              + (i % c_width) % clone_width;
            inv_cl_map[cl_map[i]].push_back(i);
          }
        }

        //--------------------------------------------------------------------------------
        inline void init_bounds()
        {
          bounds.resize(4*n_cells);

          // Compute bounds of learning square for each column
          // (r, the learning radius, is expressed as a number of columns)
          // Needs int, because of values below zero!
          for (size_type i = 0, j = 0; i != n_cells; ++i, j += 4) {
            int col_x = i % c_width, col_y = i / c_width;
            bounds[j] = std::max(col_x - (int)learn_radius, 0);
            bounds[j+1] = std::min(col_x + (int)learn_radius, (int)c_width-1);
            bounds[j+2] = std::max(col_y - (int)learn_radius, 0);
            bounds[j+3] = std::min(col_y + (int)learn_radius, (int)c_height-1);
          }
        }

        //--------------------------------------------------------------------------------
        inline bool unsafe(size_type row, size_type col) const
        {
          return !safe(row, col);
        }

        //--------------------------------------------------------------------------------
        inline bool safe(size_type row, size_type col) const
        {
          {
            NTA_ASSERT(row < c_height);
            NTA_ASSERT(col < c_width);
            NTA_ASSERT(row*c_width + col < n_cells);
          }

          return safe_cells[row*c_width + col];
        }

        //--------------------------------------------------------------------------------
        template <typename S>
        inline size_type 
        safe_offset(const S& s, diff_type row, diff_type col) const
        {
          {
            NTA_ASSERT(s.check_invariants());
          }

          size_type cell_idx = (row + s.d_row) * c_width + (col + s.d_col);

          NTA_ASSERT(cell_idx < n_cells) 
            << s << " " << cell_idx << " " << learn_radius;

          return cell_idx;
        }

        //--------------------------------------------------------------------------------
        /** NOT TESTED AT ALL
            template <typename S>
            inline void compute_all_offsets(size_type row, size_type col,
            const std::vector<S>& x,
            std::vector<size_type>& y) const 
            {
            diff_type *p = &x[0].d_row;
            diff_type *inc = &x[1].d_row - &x[0].d_row;
            diff_type *p_end = p + x.size() * inc;
            size_type k1 = row * c_width + col;

            y.resize(0);

            for (; p != p_end; p += inc) 
            y.push_back(*p * c_width + *(p+1) + k1);
            }
        */

        //--------------------------------------------------------------------------------
        template <typename S>
        inline void safe_offset(const S& s, diff_type& row, diff_type& col,
                                size_type& cell_idx) const
        {
          { // Pre-conditions
            NTA_ASSERT(0 <= row && row < (int) c_height);
            NTA_ASSERT(0 <= col && col < (int) c_width);
            NTA_ASSERT(s.check_invariants());
          } // End pre-conditions

          row += s.d_row;
          col += s.d_col;
          cell_idx = row * c_width + col;

          NTA_ASSERT(cell_idx < n_cells);
        }

        //------------------------------------------------------------------------------- 
        /**
         * Watch out when calling check_offset in a loop to reinitialize row and col
         * to the right value, if several synapses are applied to the same point!!!
         */
        template <typename S>
        inline bool 
        check_offset(const S& synapse, 
                     diff_type& row, diff_type& col, size_type& cell_idx) const
        {
          { // Pre-conditions
            NTA_ASSERT(0 <= row && row < (int) c_height);
            NTA_ASSERT(0 <= col && col < (int) c_width);
            NTA_ASSERT(synapse.check_invariants());
          } // End pre-conditions

          row += synapse.d_row;
          if (row >= 0 && row < (int) c_height) {
            col += synapse.d_col;
            if (col >= 0 && col < (int) c_width) {
              cell_idx = row * c_width + col;
              NTA_ASSERT(cell_idx < n_cells);
              return true;
            }
          }

          return false;
        }

      public:
        //--------------------------------------------------------------------------------
        inline std::string get_version() const { return std::string("cells_v2"); }
        inline size_t n_bytes() const { return 0; }
        inline size_type nCells() const { return n_cells; }
        inline size_type nMasters() const { return n_masters; }
        inline bool isCloned() const { return clone_height > 0; }
        inline size_type learnRadius() const { return learn_radius; }
        inline size_type cellsHeight() const { return c_height; }
        inline size_type cellsWidth() const { return c_width; }
        
        inline std::pair<size_type, size_type> getCoincidenceFieldShape() const 
        {
          return std::make_pair(c_height, c_width);
        }
  
        inline std::pair<size_type, size_type> getCloningShape() const
        {
          return std::make_pair(clone_height, clone_width);
        }

        //--------------------------------------------------------------------------------
        inline void traceOn(Debug what)
        {
          debug_flags.insert(what);
        }

        //--------------------------------------------------------------------------------
        inline void traceOff(Debug what)
        {
          debug_flags.erase(what);
        }

        //--------------------------------------------------------------------------------
        inline void set_max_n_segments_per_cell(size_type n)
        {
          NTA_ASSERT(0 < n);

          max_n_segs_per_cell = n;
          for (size_type i = 0; i != n_cells; ++i)
            segment_activity[i].resize(max_n_segs_per_cell);
        }
  
        //--------------------------------------------------------------------------------
        /**
         * Returns the total number of segments in this instance of Cells.
         */
        inline size_type numSegments(bool includeEmpty =false) const 
        {
          size_type n = 0;
          if (includeEmpty)
            for (size_type i = 0; i != n_masters; ++i)
              n += branches[i].nAllocatedSegments();
          else
            for (size_type i = 0; i != n_masters; ++i)
              n += branches[i].nActiveSegments();
          return n;
        }

        //--------------------------------------------------------------------------------
        inline size_type numSegmentsOnCell(size_type cell_idx) const
        {
          NTA_ASSERT(0 <= cell_idx && cell_idx < n_cells);
    
          return numSegmentsOnMaster(cl_map[cell_idx]);
        }

        //--------------------------------------------------------------------------------
        inline size_type numSynapses(value_type threshold =0) const 
        {
          size_type n = 0;
          for (size_type i = 0; i != n_masters; ++i) 
            n += branches[i].nSynapsesAboveThreshold(threshold);
          return n;
        }

        //--------------------------------------------------------------------------------
        inline size_type getMaxSegmentsInAnyCell() const
        {
          size_type n = 0;
          for (size_type i = 0; i != n_masters; ++i) 
            n = std::max(n, branches[i].nAllocatedSegments());
          return n;
        }

        //--------------------------------------------------------------------------------
        inline size_type numSynapsesMax() const
        {
          size_type n = 0;
          for (size_type i = 0; i != n_masters; ++i) 
            n = std::max(n, branches[i].nSynapsesMax());
          return n;
        }

        //--------------------------------------------------------------------------------
        inline size_type numSegmentsOnMaster(size_type master_idx) const
        {
          NTA_ASSERT(0 <= master_idx && master_idx < nMasters());
    
          return branches[master_idx].nAllocatedSegments();
        }

        //--------------------------------------------------------------------------------
        inline size_type 
        numSynapsesOnMasterSegment(size_type master_idx, size_type seg_idx) const
        {
          NTA_ASSERT(0 <= master_idx && master_idx < nMasters());
          NTA_ASSERT(0 <= seg_idx && seg_idx < branches[master_idx].nAllocatedSegments());
    
          return branches[master_idx][seg_idx].size();
        }

        //--------------------------------------------------------------------------------
        inline size_type numSynapsesOnCellSegment(size_type cell_idx, size_type seg_idx,
                                                  bool skipOutOfBounds =false) const
        {
          NTA_ASSERT(0 <= cell_idx && cell_idx < n_cells);
          NTA_ASSERT(0 <= seg_idx 
                     && seg_idx < branches[cl_map[cell_idx]].nAllocatedSegments());
    
          size_type master_idx = cl_map[cell_idx];

          if (!skipOutOfBounds) {

            return numSynapsesOnMasterSegment(master_idx, seg_idx);

          } else {

            size_type n_valid_synapses = 0;
            const Segment<U,I,T>& seg = branches[master_idx][seg_idx];

            for (size_type s = 0; s < seg.size(); ++s) {

              diff_type cell_row = cell_idx / c_width;
              diff_type cell_col = cell_idx % c_width;
              size_type c_idx = 0;

              if (check_offset(seg[s], cell_row, cell_col, c_idx))
                ++ n_valid_synapses;
            }

            return n_valid_synapses;
          }
        }

        //--------------------------------------------------------------------------------
        template <typename It1, typename It2>
        inline size_type getAbsSynapsesOnCellSegment(size_type cell_idx,
                                                     size_type seg_idx,
                                                     It1 src_cell_indices,
                                                     It2 src_strengths) const
        {
          NTA_ASSERT(0 <= cell_idx && cell_idx < n_cells);
          NTA_ASSERT(0 <= seg_idx 
                     && seg_idx < branches[cl_map[cell_idx]].nAllocatedSegments());

          size_type n_valid_synapses = 0;
          size_type master_idx = cl_map[cell_idx];
          const Segment<U,I,T>& seg = branches[master_idx][seg_idx];
    
          for (size_type s = 0; s < seg.size(); ++s) {

            diff_type cell_row = cell_idx / c_width;
            diff_type cell_col = cell_idx % c_width;
            size_type src_cell_idx;

            if (check_offset(seg[s], cell_row, cell_col, src_cell_idx)) {

              ++ n_valid_synapses;
              *src_cell_indices++ = src_cell_idx;
              *src_strengths++ = seg[s].strength;
            } 
          }

          return n_valid_synapses;
        }

        //--------------------------------------------------------------------------------
        inline void
        getSynapseOnMasterSegment(size_type master_idx, size_type seg_idx,
                                  size_type syn_idx,
                                  value_type &strength,
                                  diff_type &d_row, diff_type &d_col) const
        {
          NTA_ASSERT(0 <= master_idx && master_idx < n_masters);
          NTA_ASSERT(0 <= seg_idx && seg_idx < branches[master_idx].nAllocatedSegments());
          NTA_ASSERT(0 <= syn_idx && syn_idx < branches[master_idx][seg_idx].size());

          const Synapse<U,I,T> &synapse = branches[master_idx][seg_idx][syn_idx];
    
          strength = synapse.strength;
          d_row = synapse.d_row;
          d_col = synapse.d_col;
        }
  
        //--------------------------------------------------------------------------------
        inline void
        getSynapseOnCellSegment(size_type cell_idx, size_type seg_idx,
                                size_type syn_idx,
                                value_type &permanence,
                                diff_type &d_row, diff_type &d_col) const 
        {
          NTA_ASSERT(0 <= cell_idx && cell_idx < n_cells);

          size_type master_idx = cl_map[cell_idx];

          getSynapseOnMasterSegment(master_idx, seg_idx, syn_idx,
                                    permanence, d_row, d_col);
        }

        //--------------------------------------------------------------------------------
        inline size_type addSegment(size_type cell_idx)
        {
          NTA_ASSERT(0 <= cell_idx && cell_idx < n_cells);

          size_type master_idx = cl_map[cell_idx];
          size_type seg_idx = branches[master_idx].getFreeSegment();

          size_type n = inv_cl_map[master_idx].size();
          for (size_type i = 0; i != n; ++i)
            if (segment_activity[inv_cl_map[master_idx][i]].size() <= seg_idx)
              segment_activity[inv_cl_map[master_idx][i]].resize(seg_idx + 1);

          NTA_ASSERT(branches[master_idx][seg_idx].empty());

          return seg_idx;
        }

        //--------------------------------------------------------------------------------
        template <typename It>
        inline void addSynapses(size_type dst_cell_idx, size_type dst_seg_idx,
                                size_type n_to_add, It src_cells)
        {
          { // Pre-conditions
            NTA_ASSERT(dst_cell_idx < n_cells);
            NTA_ASSERT(branches[cl_map[dst_cell_idx]].isActiveSegment(dst_seg_idx));
            for (size_type i = 0; i != n_to_add; ++i)
              NTA_ASSERT(src_cells[i] < nCells());
            NTA_ASSERT(0 < n_to_add);
          } // End pre-conditions

          //Timer tas;

          diff_type dst_row = dst_cell_idx / c_width;
          diff_type dst_col = dst_cell_idx % c_width;
          diff_type dst_master = cl_map[dst_cell_idx];
          Segment<U,I,T>& dst_seg = branches[dst_master][dst_seg_idx];
          
          std::vector<diff_type> src_masters_deltas;

          n_modified_synapses += n_to_add;
          
          for (size_type i = 0; i != n_to_add; ++i) {

            diff_type src_row = src_cells[i] / c_width;
            diff_type src_col = src_cells[i] % c_width;
            diff_type src_master = cl_map[src_cells[i]];
            src_masters_deltas.push_back(src_master);

            diff_type d_row = dst_row - src_row;
            diff_type d_col = dst_col - src_col;
            src_masters_deltas.push_back(-d_row);
            src_masters_deltas.push_back(-d_col);

            OutSynapse<U,I,T> s(dst_seg_idx, d_row, d_col, this);
            if (is_in(s, all_out_synapses[src_master])) {
              cout << "Outgoing synapse", s, 
                "already on master", src_master, ":",
                all_out_synapses[src_master], endl;
              cout << "src_master_deltas", src_masters_deltas,
                "dst_master", dst_master,
                "dst_seg", dst_seg, endl;
            }
            NTA_ASSERT(not_in(s, all_out_synapses[src_master]));
            all_out_synapses[src_master].push_back(s);

            master_deltas[src_master].add_new(s);
          }

          dst_seg.addSynapses(dst_master, src_masters_deltas, syn_init_perm, this);

          //add_synapses_time += tas.elapsed();

          { // Post-conditions
            NTA_ASSERT(debug_check_synapses());
          }
        }

        //--------------------------------------------------------------------------------
        // TODO: group the removal of many synapses at once, if possible
        inline void 
        deleteSynapse(size_type dst_master_idx, size_type dst_seg_idx, size_type syn_idx)
        {
          { // Pre-conditions
            NTA_ASSERT(dst_master_idx < n_masters);
            NTA_ASSERT(dst_seg_idx < branches[dst_master_idx].nAllocatedSegments());
            NTA_ASSERT(!branches[dst_master_idx][dst_seg_idx].empty());
            NTA_ASSERT(syn_idx < branches[dst_master_idx][dst_seg_idx].size());
          } // End pre-conditions

          //Timer tds;

          ++n_modified_synapses;

          Segment<U,I,T>& dst_seg = branches[dst_master_idx][dst_seg_idx];
          Synapse<U,I,T>& syn = dst_seg[syn_idx];
          size_type src_master_idx = syn.src_master;
          OutSynapses& out_syns = all_out_synapses[src_master_idx];
          
          // order of synapses in all_out_synapses doesn't matter
          for (size_type i = 0; i != out_syns.size(); ++i) 
            if (out_syns[i].dst_seg == dst_seg_idx && reciprocal(syn, out_syns[i])) {
              master_deltas[src_master_idx].add_del(out_syns[i]);
              std::swap(out_syns[i], out_syns[out_syns.size()-1]);
              out_syns.pop_back();
              break;
            }

          dst_seg.removeSynapse(syn_idx);

          if (dst_seg.empty())
            branches[dst_master_idx].releaseSegment(dst_seg_idx);

          //delete_synapses_time += tds.elapsed();

          { // Post-conditions
            NTA_ASSERT(debug_check_synapses());
          }
        }

        //--------------------------------------------------------------------------------
        inline void releaseSegment(size_type cell_idx, size_type seg_idx)
        {
          { // Pre-conditions
            NTA_ASSERT(cell_idx < n_cells);
            NTA_ASSERT(seg_idx < branches[cl_map[cell_idx]].nAllocatedSegments());
          } // End pre-conditions

          //Timer trs;

          size_type master_idx = cl_map[cell_idx];
          Segment<U,I,T>& segment = branches[master_idx][seg_idx];

          if (segment.size() <= seg_empty_th) 
            for (int s = (int) segment.size() - 1; 0 <= s; --s)
              deleteSynapse(master_idx, seg_idx, s);
    
          //release_segment_time += trs.elapsed();

          { // Post-conditions
            //NTA_ASSERT(debug_check_synapses());
            // checked in deleteSynapse
          }
        }

        //--------------------------------------------------------------------------------
        template <typename It1, typename It2>
        inline size_type 
        computeSegmentActivations(It1 activities, It1 activities_end,
                                  nta::SparseMatrix<size_type,value_type>* segActivations,
                                  It2 bestCellIndices, 
                                  It2 bestSegmentIndices,
                                  It2 bestCellActivations,
                                  size_type thresholdForBest, 
                                  size_type thresholdForActive) 
        {
          {
            NTA_ASSERT(0 < thresholdForBest);
          }

          using namespace std;

          // First time only
          if (cached_threshold_for_best == std::numeric_limits<size_type>::max()) {
            cached_threshold_for_best = thresholdForBest;
            cached_threshold_for_active = thresholdForActive;
          }

          //++n_iterations;

          //Timer tpc1;

          for (size_type k = 0; k != prev_active.size(); ++k) {
            
            size_type cell_idx = prev_active[k];
            size_type src_master_idx = cl_map[cell_idx];
            diff_type src_row = cell_idx / c_width;
            diff_type src_col = cell_idx % c_width;

            // todo: replace with update
            if (safe(src_row, src_col)) {
              
              OutSynapses& news = master_deltas[src_master_idx].new_synapses;
              
              for (size_type j = 0; j != news.size(); ++j) {
                size_type dst_seg = news[j].dst_seg;
                size_type dst_cell_idx = safe_offset(news[j], src_row, src_col);
                ++ segment_activity[dst_cell_idx][dst_seg];
                ++ cell_activity[dst_cell_idx];
                changed[dst_cell_idx] = 1;
              }
              
              OutSynapses& dels = master_deltas[src_master_idx].del_synapses;
              
              for (size_type j = 0; j != dels.size(); ++j) {
                size_type dst_seg = dels[j].dst_seg;
                size_type dst_cell_idx = safe_offset(dels[j], src_row, src_col);
                -- segment_activity[dst_cell_idx][dst_seg];
                -- cell_activity[dst_cell_idx];
                changed[dst_cell_idx] = 1;
              }

            } else { // unsafe source cell, need to check offsets
  
              OutSynapses& news = master_deltas[src_master_idx].new_synapses;
              
              for (size_type j = 0; j != news.size(); ++j) {
                size_type dst_seg = news[j].dst_seg;
                diff_type dst_row = src_row, dst_col = src_col;
                size_type dst_cell_idx;
                if (check_offset(news[j], dst_row, dst_col, dst_cell_idx)) {
                  ++ segment_activity[dst_cell_idx][dst_seg];
                  ++ cell_activity[dst_cell_idx];
                  changed[dst_cell_idx] = 1;
                }
              }
              
              OutSynapses& dels = master_deltas[src_master_idx].del_synapses;
              
              for (size_type j = 0; j != dels.size(); ++j) {
                size_type dst_seg = dels[j].dst_seg;
                diff_type dst_row = src_row, dst_col = src_col;
                size_type dst_cell_idx;
                if (check_offset(dels[j], dst_row, dst_col, dst_cell_idx)) {
                  -- segment_activity[dst_cell_idx][dst_seg];
                  -- cell_activity[dst_cell_idx];
                  changed[dst_cell_idx] = 1;
                }
              }
            }
          }

          //deltas_time += tpc1.elapsed();

          //Timer tpc2;

          to_dense_01(activities, activities_end, activity);

          for (size_type src_cell_idx = 0; src_cell_idx != n_cells; ++src_cell_idx) {
      
            short diff = (short) activity[src_cell_idx] 
              - (short) prev_activity[src_cell_idx];
      
            if (diff == 0)
              continue;

            size_type src_master_idx = cl_map[src_cell_idx];
            OutSynapses& osv = all_out_synapses[src_master_idx];
            diff_type src_row = src_cell_idx / c_width;
            diff_type src_col = src_cell_idx % c_width;

            if (safe(src_row, src_col)) {
                
              OutSynapse<U,I,T>* o = &osv[0], *o_end = o + osv.size();
        
              for (; o != o_end; ++o) {
          
                size_type dst_seg = o->dst_seg;
                size_type dst_cell_idx = safe_offset(*o, src_row, src_col);
                segment_activity[dst_cell_idx][dst_seg] += diff;
                cell_activity[dst_cell_idx] += diff;
                changed[dst_cell_idx] = 1;
              }
              
            } else {

              //n_checks += osv.size();
              OutSynapse<U,I,T>* o = &osv[0], *o_end = o + osv.size();

              for (; o != o_end; ++o) {
                
                diff_type dst_row = src_row, dst_col = src_col;
                size_type dst_cell_idx;
                
                if (check_offset(*o, dst_row, dst_col, dst_cell_idx)) {
                  size_type dst_seg = o->dst_seg;
                  segment_activity[dst_cell_idx][dst_seg] += diff;
                  cell_activity[dst_cell_idx] += diff;
                  changed[dst_cell_idx] = 1;
                }
              }
            }
          }

          // CHECK
          /*
          for (size_type i = 0; i != n_cells; ++i) {
            if (cell_activity[i] < 0) {
              cout << "Negative cell activity ", i, endl;
              exit(-1);
            }
            for (size_type j = 0; j != max_n_segs_per_cell; ++j)
              if (segment_activity[i][j] < 0) {
                cout << "Negative segment activity", i, j, endl;
                exit(-1);
              }
          }
          */
          // CHECK

          copy(activity, prev_activity);

          prev_active.clear();
          for (It1 it = activities; it != activities_end; ++it)
            prev_active.push_back(*it);

          //Timer tcs;
          size_type n_activations = 0;

          for (size_type cell_idx = 0; cell_idx != n_cells; ++cell_idx) {

            if ((value_type) cell_activity[cell_idx] < thresholdForBest)
              continue;

            std::vector<size_type> inds;
            std::vector<value_type> nz;

            size_type max_activity = thresholdForBest - 1;
            size_type max_seg_idx = 0;

            if (changed[cell_idx] == 1
                || thresholdForBest != cached_threshold_for_best
                || thresholdForActive != cached_threshold_for_active) {
              
              Branch<U,I,T>& branch = branches[cl_map[cell_idx]];
              size_type n_segments = branch.nAllocatedSegments();
            
              for (size_type seg_idx = 0; seg_idx != n_segments; ++seg_idx) {

                if (branch[seg_idx].size() < max_activity)
                  continue;

                size_type seg_activity = segment_activity[cell_idx][seg_idx];
              
                if (segActivations && seg_activity >= thresholdForActive) {
                  inds.push_back(seg_idx);
                  nz.push_back(seg_activity);
                }
        
                if (max_activity < seg_activity) {
                  max_seg_idx = seg_idx;
                  max_activity = seg_activity;
                }
              }

              cache[cell_idx].max_seg_idx = max_seg_idx;
              cache[cell_idx].max_activity = max_activity;
              copy(inds, cache[cell_idx].active_segs);
              copy(nz, cache[cell_idx].active_levels);
              changed[cell_idx] = 0;

            } else {

              max_seg_idx = cache[cell_idx].max_seg_idx;
              max_activity = cache[cell_idx].max_activity;
              copy(cache[cell_idx].active_segs, inds);
              copy(cache[cell_idx].active_levels, nz);
            }            

            if (thresholdForBest <= max_activity) {
              *bestCellIndices++ = cell_idx;
              *bestSegmentIndices++ = max_seg_idx;
              *bestCellActivations++ = max_activity;
              ++n_activations;
            }

            if (segActivations) 
              segActivations->setRowFromSparse(cell_idx, 
                                               inds.begin(), inds.end(), 
                                               nz.begin());
          }

          // Do it only when all the cells and segments
          // have been examined!
          cached_threshold_for_best = thresholdForBest;
          cached_threshold_for_active = thresholdForActive;

          for (size_type i = 0; i != n_masters; ++i)
            master_deltas[i].clear();

          //act_time += tcs.elapsed();

          { // Post-conditions
            // no change to the synapses here
            //NTA_ASSERT(debug_check_synapses());
          }

          return n_activations; // accomodates back_inserter
        }

        //--------------------------------------------------------------------------------
        /*
        std::vector<int> debug_get_cell_activity_levels() const
        {
          return cell_activity.board;
        }

        //--------------------------------------------------------------------------------
        std::vector<short> debug_get_segment_activity_levels() const
        {
          std::vector<short> r;
          r.resize(n_cells*max_n_segs_per_cell);
          for (size_type i = 0; i != n_cells; ++i) {
            for (size_type j = 0; j != max_n_segs_per_cell; ++j)
              r[i*max_n_segs_per_cell+j] = segment_activity[i].board[j];
          }
          return r;
        }
        */ 

        //--------------------------------------------------------------------------------
        // UPDATE
        //--------------------------------------------------------------------------------
      private:
        template <typename It1>
        inline void get_candidates(size_type dst_cell, It1 src_cells, It1 src_cells_end)
        {
          //Timer tgc;
          NTA_ASSERT(dst_cell < n_cells);

          size_type dst_col = 4 * dst_cell;
          candidates.resize(0);

          for (It1 e = src_cells; e != src_cells_end; ++e) {
            size_type col = *e;
            if (existing_src[col])
              continue;
            size_type col_x = col % c_width, col_y = col / c_width;
            if (bounds[dst_col] <= col_x && col_x <= bounds[dst_col+1]
                && bounds[dst_col+2] <= col_y && col_y <= bounds[dst_col+3]) 
              candidates.push_back(col);
          }
          //get_candidates_time += tgc.elapsed();
        }

        //--------------------------------------------------------------------------------
        // TODO: document instruction language:
        /**
         * seg_idx = -1 = create new segment
         * n_syn_to_add = -1 = strengthen
         * n_syn_to_add = -2 = orphan forgetting
         * touched_segs is as most n_instructions long
         */
      public:
        template <typename It1, typename It2, typename It3>
        inline size_type update(It1 input, It1 input_end, 
                                size_type nInstructions, It2 instruction,
                                It3 touched_segs)
        {
          using namespace std;

          //Timer tu;

          size_type n_touched_segs = 0;
          to_dense_01(input, input_end, dense_input);

          for (size_type k = 0; k != nInstructions; ++k) {

            ++n_instructions_processed;
            size_type cell_idx = *instruction++;
            long_diff_type seg_idx = *instruction++;
            long_diff_type n_syn_to_add = *instruction++;
            size_type master_idx = cl_map[cell_idx];
            size_type cell_row = cell_idx / c_width;
            size_type cell_col = cell_idx % c_width;
    
            NTA_ASSERT(cell_idx < n_cells);
            NTA_ASSERT(seg_idx == -1 || 0 <= seg_idx);
            NTA_ASSERT(n_syn_to_add == -1 || n_syn_to_add == -2 || n_syn_to_add > 0);

            // make sure we don't pick ourselves
            // ok to have the same master if delta != 0,
            // but here we are talking about _cells_ indices,
            // not master indices.
            existing_src.clear();
            existing_src.set(cell_idx);

            if (seg_idx < 0)  {
      
              NTA_ASSERT(n_syn_to_add > 0);

              // always adding to new segment
              // seg_idx can be anything!

              seg_idx = addSegment(cell_idx);
              
              NTA_ASSERT(seg_idx < (int) branches[master_idx].nAllocatedSegments());
              NTA_ASSERT(seg_idx < (int) segment_activity[cell_idx].size());

            } else {

              NTA_ASSERT(seg_idx < (int) branches[master_idx].nAllocatedSegments());
              NTA_ASSERT(seg_idx < (int) segment_activity[cell_idx].size());

              Segment<U,I,T>& seg = branches[master_idx][seg_idx];

              // Don't modify a segment that has been freed by a previous instruction.
              // This is allowed to speed up conflict resolution.
              if (seg.empty()) {
                NTA_ASSERT(n_syn_to_add < 0);
                continue;
              }

              // adjust segment strengths: -2: orphan forgetting.
              // otherwise, -1 or positive number
              value_type active_inc = 
                n_syn_to_add == -2 ? -syn_perm_orphan_dec : syn_perm_match_inc;

              value_type inactive_inc = 
                n_syn_to_add == -2 ? 0.0 : -syn_perm_mix_match_dec;

              bool check = unsafe(cell_row, cell_col);
             
              for (int i = seg.size() - 1; 0 <= i; --i) {

                Synapse<U,I,T>& syn = seg[i];
                diff_type src_row = cell_row, src_col = cell_col;
                size_type src_cell_idx;

                if (check) {
                  if (!check_offset(syn, src_row, src_col, src_cell_idx))
                    continue;
                } else 
                  src_cell_idx = safe_offset(syn, src_row, src_col);

                value_type inc = dense_input[src_cell_idx] ? active_inc : inactive_inc;

                if (inc == 0) {
                  existing_src.set(src_cell_idx);
                  continue;
                }

                NTA_ASSERT(syn_min_perm <= syn.strength);
                syn.strength += inc;

                if (syn.strength < syn_min_perm) {

                  deleteSynapse(cl_map[cell_idx], seg_idx, i);

                } else {
                  existing_src.set(src_cell_idx);
                }
              }
            } // else (seg_idx >= 0)

            if (n_syn_to_add > 0) {

              get_candidates(cell_idx, input, input_end);
              random_shuffle(candidates.begin(), candidates.end(), rng);
              n_syn_to_add = min((size_type) n_syn_to_add, (size_type) candidates.size());
              if (n_syn_to_add > 0) 
                addSynapses(cell_idx, seg_idx, n_syn_to_add, candidates.begin());
            }

            if (branches[master_idx][seg_idx].size() <= seg_empty_th) {

              releaseSegment(cell_idx, seg_idx);

            } else {

              *touched_segs++ = cell_idx;
              *touched_segs++ = seg_idx;
              ++n_touched_segs;
            }
          }

          //update_time += tu.elapsed();

          NTA_ASSERT(debug_check_synapses());

          return n_touched_segs;
        }

        //--------------------------------------------------------------------------------
        // TODO: change that to registration mechanism?
        inline size_type
        decaySynapses(value_type decay_rate, value_type deleteIfLessThan =-1)
        {
          //Timer tds;

          size_type nn = 0;

          if (deleteIfLessThan < 0) 
            deleteIfLessThan = syn_min_perm;

          for (size_type m = 0; m < n_masters; m++) {

            std::vector< Segment<U,I,T> >& segments = branches[m].getAllSegments();

            for (size_type seg_idx = 0; seg_idx != segments.size(); ++seg_idx) {

              Segment<U,I,T>& seg = segments[seg_idx];

              if (seg.empty()) 
                continue;

              for (int i = seg.size() - 1; 0 <= i; --i) {

                Synapse<U,I,T>& synapse = seg[i];
                synapse.strength -= decay_rate;

                if (synapse.strength < deleteIfLessThan) {
                  ++nn;
                  deleteSynapse(m, seg_idx, i);
                }
              }
            }
          }

          //decay_time += tds.elapsed();
          NTA_ASSERT(debug_check_synapses());

          return nn;
        }
        
        //--------------------------------------------------------------------------------
        // STATISTICS
        //--------------------------------------------------------------------------------
        /*
         * This prints internal stats, counts and timings that are useful for optimizing.
         */
        inline void print_stats(bool humanReadable =true) const
        {
          if (humanReadable) {

            double pct_cells_active 
              = 100.0 * n_cells_active / (n_cells * n_iterations);

            //double pct_act_change_cells 
            //  = 100.0 * n_act_change_cells / (n_cells * n_iterations);
            
            cout << setprecision(8);
            cout 
              , "n iterations              = ", n_iterations, endl
              , "n cells                   = ", n_cells, endl
              , "n masters                 = ", n_masters, endl
              , "n segments                = ", numSegments(), endl
              , "n synapses                = ", numSynapses(), endl
              , "n instructions            = ", n_instructions_processed, endl
              , "n cells active            = ", n_cells_active, endl
              , "% cells active / iter     = ", pct_cells_active, endl
              , "n checks                  = ", n_checks, endl
              , "n no checks               = ", n_no_checks, endl
              , "n segs to clear           = ", n_segs_to_clear, endl
              , "n cells to clear          = ", n_cells_to_clear, endl
              , "n modified synapses       = ", n_modified_synapses, endl
              //, "% act ch cells /iter      = ", pct_act_change_cells, endl
              //, "n segments visited        = ", n_segments_visited, endl
              , "n synapses visited        = ", n_synapses_visited, endl
              , endl
              , "Times ==============", endl
              //, "num syn            = ", num_syn_time, endl
              //, "abs syn            = ", abs_syn_time, endl
              //, "valid offset       = ", valid_offset_time, endl
              , "clear              = ", clear_time, endl
              , "deltas prop        = ", deltas_time, endl
              , "prop               = ", prop_time, endl
              //, "|offsets           = ", offset_time, endl
              //, "|seg prop          = ", seg_prop_time, endl
              //, "|cell prop         = ", cell_prop_time, endl
              , "activation         = ", act_time, endl
              , "update             = ", update_time, endl
              //, "|densify           = ", densify_time, endl
              //, "|get candidates    = ", get_candidates_time, endl
              //, "|add syn in update = ", add_syn_time_in_update, endl
              , "delete syn (all)   = ", delete_synapses_time, endl
              , "add syn (all)      = ", add_synapses_time, endl
              , "release seg (all)  = ", release_segment_time, endl
              , "decay time         = ", decay_time, endl;

          } else {

            cout << setprecision(8);
            cout << n_iterations << "  " 
                 << nCells() << " "
                 << n_masters << " "
                 << numSegments() << " "
                 << numSynapses() << " "
                 << n_bytes() << "  "
                 << n_cells_active << " "
                 << n_segments_visited << " "
                 << n_synapses_visited << "  "
                 << prop_time << " " 
                 << act_time << " "
                 << update_time << " "
                 << decay_time << " "
                 << std::endl;
          }
        }

        //--------------------------------------------------------------------------------
        // PERSISTENCE
        //--------------------------------------------------------------------------------
        /**
         * TODO: compute, rather than writing to a buffer.
         * TODO: move persistence to binary, faster and easier to compute expecte size.
         */
        inline size_type persistent_size() const
        {
          size_type size = 0;
          for (size_type i = 0; i != n_masters; ++i) 
            size += branches[i].persistent_size() + 2;
          return size + 1024;
        }

        //--------------------------------------------------------------------------------
        inline void save(std::ostream& out_stream) const
        {
          NTA_ASSERT(out_stream.good());
          NTA_ASSERT(debug_check_synapses());

          out_stream << get_version() << ' '
                     << rng << ' '
                     << n_cells << ' ' 
                     << n_masters << ' '
                     << c_height << ' ' << c_width << ' '
                     << clone_height << ' ' << clone_width << ' '
                     << learn_radius << ' ' << learn_area << ' '
                     << syn_init_perm << ' '
                     << syn_min_perm << ' '
                     << syn_perm_orphan_dec << ' '
                     << syn_perm_match_inc << ' '
                     << syn_perm_mix_match_dec << ' '
                     << seg_empty_th << ' '
                     << max_n_segs_per_cell << ' '
                     << std::endl;
        
          for (size_type i = 0; i != n_masters; ++i) {
            branches[i].save(out_stream);
            out_stream << std::endl;
          }
        }

        //--------------------------------------------------------------------------------
        /**
         * Need to load and re-propagate activities so that we can really persist
         * at any point, load back and resume inference at exactly the same point.
         */
        inline void load(std::istream& in_stream)
        {
          NTA_ASSERT(in_stream.good());

          std::string tag = "";
          in_stream >> tag;

          if (tag != get_version()) {
            std::cout << "Can't load Cells format: " << tag << std::endl;
            exit(-1);
          }

          in_stream >> rng 
                    >> n_cells  
                    >> n_masters 
                    >> c_height >> c_width 
                    >> clone_height >> clone_width 
                    >> learn_radius >> learn_area 
                    >> syn_init_perm 
                    >> syn_min_perm 
                    >> syn_perm_orphan_dec 
                    >> syn_perm_match_inc 
                    >> syn_perm_mix_match_dec
                    >> seg_empty_th
                    >> max_n_segs_per_cell;
          
          branches.resize(n_masters);
        
          for (size_type i = 0; i != n_masters; ++i) 
            branches[i].load(in_stream);
          
          // Reconstruct all_out_synapses
          all_out_synapses.resize(n_masters);

          size_type M = 0;
          for (size_type i = 0; i != n_masters; ++i) {
            for (size_type j = 0; j != branches[i].nAllocatedSegments(); ++j) {
              if (branches[i][j].empty()) // no free segment in save, though
                continue;
              const Segment<U,I,T>& seg = branches[i][j];
              for (size_type k = 0; k != seg.size(); ++k) {
                const Synapse<U,I,T>& in_synapse = seg[k];
                OutSynapse<U,I,T> out_synapse(j, -in_synapse.d_row, -in_synapse.d_col);
                all_out_synapses[in_synapse.src_master].push_back(out_synapse);
              }
              M = std::max(M, j);
            }
          }

          finish_init();

          // we probably can remove that if we do the right thing
          // in addSegment
          for (size_type i = 0; i != n_cells; ++i)
            segment_activity[i].resize(M+1, 0);

          NTA_ASSERT(debug_check_synapses());
        }

        //--------------------------------------------------------------------------------
        // DEBUG
        //--------------------------------------------------------------------------------
        /*
         * This routine cross-checks that the synapses are all set up correctly, both 
         * the incoming synapses on each segment and the outgoing synapses.
         * This can take a lot of time if there are lots of cells/synapses, but it 
         * is very valuable in debugging.
         */
        bool debug_check_synapses() const
        {
          return true;

          // Just in case we have a debug build, but we don't want to 
          // check the synapses
          //if (!is_in(cross_check_synapses, debug_flags))
          //  return true;

          using namespace std;

          set<string> back_map;
          set<string> forward_map;

          //std::cout << "Verifying synapses (may take time)...";
          bool consistent = true;

          for (size_type i = 0; i != n_masters; ++i) {
            for (size_type j = 0; j != branches[i].nAllocatedSegments(); ++j) {

              const Segment<U,I,T>& seg = branches[i][j];

              for (size_type k = 0; k != seg.size(); ++k) {
                
                if (!seg[k].check_invariants(this)) {
                  std::cout << "\nIncoming synapse: " << seg[k] 
                            << " has incorrect state"
                            << std::endl;
                  consistent = false;
                }
                
                stringstream buf;
                buf << seg[k].src_master << "," << j << " " 
                    << seg[k].neg_delta().first << "," << seg[k].neg_delta().second;

                if (is_in(buf.str(), back_map)) {
                  cout << "\nDuplicate incoming synapse: ", seg[k], endl;
                  consistent = false;
                }

                back_map.insert(buf.str());
              }
            }
            
            for (size_type j = 0; j != all_out_synapses[i].size(); ++j) {
              
              const OutSynapse<U,I,T>& syn = all_out_synapses[i][j];
              
              if (!syn.check_invariants(this)) {
                std::cout << "\nOutgoing synapse: " << syn
                          << " has incorrect state" 
                          << std::endl;
                consistent = false;
              }

              // Outgoings are unique between a src and dst masters when taking 
              // into account the seg id,
              // i.e. we allow outgoings from a cell to two or more different
              // segs of another cell (not the same seg though).
              stringstream buf;
              buf << i << "," << syn.dst_seg << " "
                  << syn.delta().first << "," << syn.delta().second;

              if (is_in(buf.str(), forward_map)) {
                cout << "\nDuplicate outgoing synapse:", i, syn, endl;
                consistent = false;
              }

              forward_map.insert(buf.str());
            }
          }
          
          bool r = back_map == forward_map;
          
          if (!r || !consistent) {
            std::cout << "synapses inconsistent" << std::endl;
            debug_print();
            exit(-1);
            /*
            cout << "\nBack/forward maps:" << endl;
            set<string>::iterator it1 = back_map.begin();
            set<string>::iterator it2 = forward_map.begin();
            for (; it1 != back_map.end(); ++it1, ++it2)
              cout << setw(20) << *it1 << " " << *it2 << endl;
            */
            //cout << "\nForward map:" << endl;
            //for (it = forward_map.begin(); it != forward_map.end(); ++it)
            // cout << *it << endl;
          } else {
            //std::cout << "synapses consistent" << std::endl;
          }

          return r;
        }

        //--------------------------------------------------------------------------------
        /*
         * This prints out extra information that's useful when debugging.
         */
        void debug_print() const
        {
          if (true)
            std::cout << get_version() << std::endl
                      << "n_cells                = " << n_cells << std::endl 
                      << "n_masters              = " << n_masters << std::endl
                      << "c_height               = " << c_height << std::endl 
                      << "c_width                = " << c_width << std::endl
                      << "clone_height           = " << clone_height << std::endl 
                      << "clone_width            = " << clone_width << std::endl
                      << "learn_radius           = " << learn_radius << std::endl 
                      << "learn_area             = " << learn_area << std::endl
                      << "syn_init_perm          = " << syn_init_perm << std::endl
                      << "syn_min_perm           = " << syn_min_perm << std::endl
                      << "syn_perm_orphan_dec    = " << syn_perm_orphan_dec << std::endl
                      << "syn_perm_match_inc     = " << syn_perm_match_inc << std::endl
                      << "syn_perm_mix_match_dec = " << syn_perm_mix_match_dec << std::endl
                      << "seg_empty_th           = " << seg_empty_th << std::endl
                      << std::endl;

          cout << "\n----------------------------------------" << endl;
          cout << "Cells state" << endl;
          cout << "----------------------------------------" << endl << endl;    

          std::cout << "Incoming synapses" << std::endl;
          for (size_type i = 0; i != n_masters; ++i) {
            if (!branches[i].empty()) {
              std::cout << "Master #" << i << ": ";
              std::cout << branches[i] << std::endl;
            }
          }

          std::cout << "\nOutgoing synapses" << std::endl;
          for (size_type i = 0; i != all_out_synapses.size(); ++i) {
            if (! all_out_synapses[i].empty()) {
              std::cout << "Master #" << i << ": ";
              for (size_type j = 0; j != all_out_synapses[i].size(); ++j)
                std::cout << "(" << all_out_synapses[i][j] << ")";
              std::cout << std::endl;
            }
          }

          std::cout << "\nActivity levels" << std::endl;
          for (size_type i = 0; i != n_cells; ++i) {
            if (cell_activity[i] > 0)
              std::cout << "Cell #" << i << " = " << cell_activity[i] << std::endl;
            const Branch<U,I,T>& branch = branches[cl_map[i]];
            for (size_type j = 0; j != branch.nAllocatedSegments(); ++j)
              if (!branch[j].empty() && segment_activity[i][j] > 0)
                std::cout << "\tSeg #" << j << " = "
                          << segment_activity[i][j] << std::endl;
          }
        }

        //--------------------------------------------------------------------------------
      };

    } // end namespace Cells2
  } // end namespace algorithms
} // end namespace nta

//--------------------------------------------------------------------------------
#endif // NTA_CELLS_2_HPP
