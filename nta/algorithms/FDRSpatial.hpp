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

#ifndef NTA_FDR_SPATIAL_HPP
#define NTA_FDR_SPATIAL_HPP

#include <nta/math/stl_io.hpp>

namespace nta {
  namespace algorithms {

    //--------------------------------------------------------------------------------
    /**
     * The sweeping algorithm of the continuous spatial pooler.
     */
    template <typename I, typename It>
    inline void csp_sweep(I c_field_x, I c_field_y,
                          I stimulusThreshold,
                          I inhibitionRadius,
                          It denseOutput, It denseOutput_end,
                          std::vector<I>& activeElements,
                          It afterInhibition, It afterInhibition_end)
    {
      NTA_ASSERT(denseOutput <= denseOutput_end);

      const I n_c = c_field_x * c_field_y;
      typedef greater_2nd_no_ties<I,float> Order;
      std::set<std::pair<I, float>, Order> to_visit;
      std::vector<std::pair<int, float> > visited(n_c, std::make_pair(-1,-1));

      std::fill(afterInhibition, afterInhibition_end, (nta::Real32)0);

      for (I i = 0; i != n_c; ++i)
        if (denseOutput[i] > stimulusThreshold) {
          to_visit.insert(std::make_pair(i, denseOutput[i]));
          visited[i] = std::make_pair(i, denseOutput[i]);
        }
      
      activeElements.clear();

      while (! to_visit.empty()) {

        I chosen = to_visit.begin()->first;
        activeElements.push_back(chosen);

        I cx = chosen / c_field_y;
        I cy = chosen % c_field_y;
        I xmin = (I) std::max((int)0, (int)cx - (int)inhibitionRadius);
        I xmax = std::min(cx + inhibitionRadius+1, c_field_x);
        I ymin = (I) std::max((int)0, (int)cy - (int)inhibitionRadius);
        I ymax = std::min(cy + inhibitionRadius+1, c_field_y);

        //std::cout << "Chose: " << chosen 
        //          << " with val: " << to_visit.begin()->second 
        //<< " at " << cx << "," << cy
        //          << std::endl;
        //std::cout << "xmin= " << xmin << " xmax= " << xmax
        //          << " ymin= " << ymin << " ymax= " << ymax 
        //          << std::endl;
        
        //std::cout << "inhibiting: ";

        for (I x = xmin; x != xmax; ++x)
          for (I y = ymin; y != ymax; ++y) {
            I ii = x * c_field_y + y;
            if (visited[ii].first != -1) {
              //std::cout << "(" << x << "," << y << "," << ii << ")";
              to_visit.erase(visited[ii]);
              visited[ii].first = -1;
            }
          }
        //std::cout << std::endl;

        afterInhibition[chosen] = 1;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * The FDRSpatial class stores binary 0/1 coincidences and computes the degree 
     * of match between an input vector (binary 0/1) and each coincidence, to output
     * a sparse (binary 0/1) "representation" of the input vector in terms of the 
     * coincidences. The degree of match is simply the number of bits that overlap
     * between each coincidence and the input vector. Only the top-N best matches are
     * turned on in the output, and the outputs always have the same, fixed number 
     * of bits turned on (N), according to FDR principles. 
     *
     * The coincidences can be learnt, in which case the non-zeros of the coincidences
     * that match the inputs best are reinforced while others are gradually forgotten. 
     * Learning is online and the coincidences can adapt to the changing statistics 
     * of the inputs.
     * 
     * NOTE: 
     * there are two thresholds used in this class: 
     * - stimulus_threshold is used to decide whether a coincidence matches the 
     * input vector well enough or not. It is a hurdle that the coincidence has 
     * to pass in order to participate in the representation of the input, removing
     * coincidences that would have only an insignificant number of bits matching
     * the input.
     * - histogram_threshold is used, with learning only, to decide which bits from
     * the coincidences are more important and can participate in matching the 
     * input. Bits with a count lower than histogram_threshold are kept in the 
     * coincidence, but they do not participate to match the input.
     *
     * IMPLEMENTATION NOTE:
     * Each row (coincidence) has exactly nnzpr non-zeros.
     * The non-zeros are represented by pairs (index,count) of type (uint,float),
     * and we call that type 'IndNZ'. Since all the rows have the same number of
     * non-zeros, we use a compact storage where all the non-zeros are stored in
     * a vector (of immutable size = nrows * nnzpr), and this vector is called 
     * 'ind_nz'. The k-th non-zero of row i is at position: ind_nz[i*nnzpr+k].
     *
     * IMPLEMENTATION NOTE:
     * In order to optimize speed, the non-zeros of each coincidence are stored in 
     * such a way that the non-zeros which have a count > histogram_threshold appear
     * first, and the others after. The boundary between those two sets is maintained 
     * in ub[i] for each row i. These two sets are updated in update(). In infer(),
     * only the non-zeros up to ub[i] are used to compute the match of coincidence i
     * and the input vector.
     *
     * TODOS:
     * =====
     * 1. Separate learning from inference (don't call update in infer), which is cleaner
     * and we can call infer() without conditionally calling learn().
     * 
     * 2. Return only indices of the non-zeros from infer(), when integrating with FDR TP.
     */
    class FDRSpatial
    {
    public:
      typedef nta::UInt32 size_type;
      typedef nta::Real32 value_type;
      typedef std::pair<size_type, value_type> IndNZ;

      typedef enum { uniform, gaussian } CoincidenceType;

      //--------------------------------------------------------------------------------
      /**
       * Constructor for "discrete" SP.
       * 
       * Creates a random sparse matrix with uniformly distributed non-zeros, all the 
       * non-zeros having value 1, unless _clone is true, in which case the coincidence
       * matrix is not set here, but can be set later from a SM with set_cm. 
       * The coincidences are sparse 0/1 vectors (vertices of the unit hypercube of 
       * dimension ncols).
       *
       * Parameters:
       * ==========
       * - nbabies: the number of babies in this FDR SP
       * - nrows: the number of coincidence vectors
       * - ncols: the size of each coincidence vector (number of elements)
       * - nnzpr: number of non-zeros per row, i.e. number of non-zeros in each
       *          binary coincidence
       * - output_nnz: number of non-zeros in result vector for infer() ( <= nrows)
       * - stimulus_threshold: minimum number of bits in the input that need to 
       *          match with one coincidence for the input vector. If that threshold
       *          is not met by a pair (coincidence,input), the output for that 
       *          coincidence is zero.
       * - clone: whether to clone this spatial pooler or not. Two or more spatial
       *          poolers that are cloned share the same coincidences.
       * - coincidence_type: the type of coincidence to use. The type determines
       *          the distribution of the non-zeros inside the coincidence.
       *          Available types: uniform, gaussian. If gaussian, specify rf_x
       *          and sigma.
       * - rf_x:  length of the receptive field in each coincidence in gaussian 
       *          mode: > 0, ncols % rf_x == 0. 
       * - sigma: sigma for the gaussian distribution when using gaussian 
       *          coincidences, > 0.
       * - seed: random seed, that can be set to make runs repeatable. This seed 
       *          influences only the initial random coincidence matrix. There is 
       *          no randomness in the rest of the algorithm. 
       * - init_nz_val: initial value of the counts for each bit of each coincidence
       *          (used in learning)
       * - threshold_cte: determines histogram threshold, that is, bit count that
       *          that needs to be exceeded for coincidence bit to participate 
       *          in matching (see learning)
       * - normalization_sum: value to which the sum of the bit counts for each
       *          coincidence is normalized to (reduces the likelihood of a
       *          coincidence bit to participate in further matching, see learning)
       * - normalization_freq: how often normalization is performed
       * - hysteresis: Must be >= 1.0. == 1.0 by default. If > 1.0, then outputs that
       *          were present in the sparse output of the previous time step will 
       *          have their values multiplied by hysteresis before choosing the 
       *          winners in the current time step.
       *
       * NOTE:
       * FDRSpatial starts with learning off. 
       * 
       * IMPLEMENTATION NOTE:
       * Don't forget to initialize ub to nnzpr for each row, so that we multiply 
       * correctly in infer when not using learning. 
       */
      FDRSpatial(size_type _nbabies,
                 size_type _nrows, size_type _ncols, size_type _nnzpr, 
                 size_type _output_nnz, 
                 size_type _stimulus_threshold,
                 bool _clone =false,
                 CoincidenceType coincidence_type =uniform,
                 size_type _rf_x =0,
                 value_type _sigma =0.0f,
                 int _seed =-1,
                 value_type _init_nz_val =1.0f,
                 value_type _threshold_cte =800.0f,
                 value_type _normalization_sum =1000.0f,
                 size_type _normalization_freq =20,
                 value_type _hysteresis =1.0f)
        : nbabies(_nbabies),
          nrows(_nrows), ncols(_ncols), nnzpr(_nnzpr), iter(0),
          output_nnz(_output_nnz), 
          hysteresis(_hysteresis),
          stimulus_threshold(_stimulus_threshold),
          histogram_threshold((value_type) _threshold_cte / (value_type) nnzpr),
          normalization_sum(_normalization_sum),
          normalization_freq(_normalization_freq),
          ub(nrows, nnzpr), ind_nz(nrows * nnzpr),
          n_prev_winners(0), prev_winners(nrows, 0),
          d_output(0)
      {
        { // Pre-conditions
          NTA_ASSERT(0 < nnzpr && nnzpr <= ncols);
          NTA_ASSERT(output_nnz <= nrows);
          NTA_ASSERT(1.0 <= hysteresis);
          NTA_ASSERT(0 < histogram_threshold);
          NTA_ASSERT(0 < normalization_sum);
          NTA_ASSERT(0 < normalization_freq);
          NTA_ASSERT(ub.size() == nrows);
          for (size_type i = 0; i != ub.size(); ++i)
            NTA_ASSERT(ub[i] == nnzpr);
          NTA_ASSERT(coincidence_type == uniform 
                     || coincidence_type == gaussian);
          NTA_ASSERT(coincidence_type != gaussian 
                     || (_rf_x > 0 && _sigma > 0));
        } // End pre-conditions

        if (! _clone) {

          if (coincidence_type == uniform) 

            random_pair_sample(nrows, ncols, nnzpr, ind_nz, _init_nz_val, _seed);

          else if (coincidence_type == gaussian)

            gaussian_2d_pair_sample(nrows, ncols, nnzpr, _rf_x, _sigma, ind_nz,
                                    _init_nz_val, _seed);

          else {
            std::cout << "Unknown coincidence type: " << coincidence_type
                      << " - exiting" << std::endl;
            exit(-1);
          }
            
          normalize();
        }

        { // Post-conditions
          NTA_ASSERT(ind_nz.empty() || ind_nz.size() == nrows * nnzpr);
          for (size_type i = 0; i != ind_nz.size(); ++i) 
            NTA_ASSERT(ind_nz[i].first < ncols);
        } // End post-conditions
      }

      //--------------------------------------------------------------------------------
      /**
       * Null constructor for persistence in Python.
       */
      inline FDRSpatial() {}

      //--------------------------------------------------------------------------------
      /**
       * This version tag is used in persistence.
       */
      inline const std::string version() const { return "fdrsp_1.0"; }

      //--------------------------------------------------------------------------------
      /**
       * Various accessors.
       */
      inline size_type nBabies() const { return nbabies; }
      inline size_type nRows() const { return nrows; }
      inline size_type nCols() const { return ncols; }
      inline size_type nNonZerosPerRow() const { return nnzpr; }
      inline size_type nNonZeros() const { return nnzpr * nrows; }
      inline size_type nNonZerosInOutput() const { return output_nnz; }
      inline value_type getHysteresis() const { return hysteresis; }
      inline value_type getStimulusThreshold() const { return stimulus_threshold; }
      inline value_type getHistogramThreshold() const { return histogram_threshold; }
      inline value_type getNormalizationSum() const { return normalization_sum; }
      inline value_type getNormalizationFreq() const { return normalization_freq; }

      //--------------------------------------------------------------------------------
      inline void reset()
      {
        n_prev_winners = 0;
      }

      //--------------------------------------------------------------------------------
      /**
       * For inspectors.
       * This makes compute slower.
       */
      inline void setStoreDenseOutput(bool x) 
      { 
        if (x) {
          d_output.resize(nbabies);
          for (size_type i = 0; i != nbabies; ++i)
            d_output[i].resize(nrows);
        } else {
          d_output.resize(0);
        }
      }

      //--------------------------------------------------------------------------------
      /**
       * For inspectors, only if setStoreDenseOutput(true) was called before!
       */
      inline std::vector<value_type> getDenseOutput(size_type babyIdx) const 
      { 
        NTA_ASSERT(babyIdx < nbabies);
        NTA_ASSERT(!d_output.empty());

        return d_output[babyIdx]; 
      }

      //--------------------------------------------------------------------------------
      /**
       * For debugging.
       */
      inline std::vector<size_type> getPrevWinners() const
      {
        return
          std::vector<size_type>(prev_winners.begin(), prev_winners.begin() + n_prev_winners);
      }

      //--------------------------------------------------------------------------------
      /**
       * Mostly for debugging, returns vector of positions of last element on each row
       * that has a counter > histogram_threshold.
       */
      const std::vector<size_type>& get_ub() const { return ub; }

      //--------------------------------------------------------------------------------
      /**
       * Set our coincidences from a SM in csr format (in Python, create the string with
       * toPyString()). Resets dimensions to be dimensions of the SM. Also resets ub[i] 
       * to nnzpr. Assumes that all the rows in the SM have exactly the same number of 
       * non-zeros (assert). n_bytes is added by SM toCSR, just after the format tag, 
       * but we don't need it here: we load it and ignore it.
       *
       * NOTE: the C++ implementation of FDR SP has a single sparse matrix to store *BOTH*
       * coincidences' non-zero indices and coincidences' bit counts! Python maintains
       * two separate data structures.
       *
       * NOTE: watch out! If you use this method, it does reset ub[i] to nnzpr, i.e.
       * all the bits of all coincidences will be used for matching. 
       *
       * NOTE: the matrix passed in needs to be already normalized.
       */
      inline void set_cm(const std::string& cm_string)
      {
        {
          NTA_ASSERT(!cm_string.empty());
        }

        std::stringstream cm_stream(cm_string);

        std::string tag;
        cm_stream >> tag;
        if (tag != "csr" && tag != "sm_csr_1.5") {
          std::cout << "Unknown format for coincidence matrix: "
                    << tag << std::endl;
          exit(-1);
        }

        size_type n_bytes = 0, k = 0, nnz = 0;
        
        cm_stream >> n_bytes >> nrows >> ncols >> nnz;

        ind_nz.resize(nnz);
        ub.resize(nrows);
    
        for (size_type i = 0; i != nrows; ++i) {
      
          size_type nnz_this_row = 0;
          cm_stream >> nnz_this_row;

          if (i == 0)
            nnzpr = nnz_this_row;
          else
            if (nnz_this_row != nnzpr) {
              std::cout << "More non-zeros on row " << i
                        << " than expected (" << nnzpr << ")"
                        << std::endl;
              exit(-1);
            }

          for (size_type j = 0; j != nnzpr; ++j, ++k) {
            cm_stream >> ind_nz[k].first >> ind_nz[k].second;
            if (ind_nz[k].first >= ncols) {
              std::cout << "Column index out of bound: " << ind_nz[k].first
                        << " for non-zero #" << k 
                        << " on row " << i
                        << std::endl;
              exit(-1);
            }
          }

          ub[i] = nnzpr;
        }

        //normalize();

        {
          NTA_ASSERT(k == nnz);
          NTA_ASSERT(ind_nz.size() == nnz);
          NTA_ASSERT(ub.size() == nRows());
        }
      }

      //--------------------------------------------------------------------------------
      /**
       * Sets the coincidence matrix/histogram directly from a dense array. That makes
       * the Python code much easier (can set directly from a numpy dense array).
       */
      template <typename It>
      inline void set_cm_from_dense(It begin, It end)
      {
        {
          NTA_ASSERT((size_type)(end - begin) == nrows * ncols);
          NTA_ASSERT(ind_nz.size() == nrows * nnzpr);
        }

        size_type k = 0;

        for (size_type i = 0; i != nrows; ++i) {
          for (size_type j = 0; j != ncols; ++j) {
            if (begin[i*ncols+j] != 0) 
              ind_nz[k++] = std::make_pair(j, begin[i*ncols+j]);
          }
          if (k != (i+1) * nnzpr) {
            std::cout << "Wrong number of non-zeros on row " << i
                      << " - expected: " << nnzpr
                      << " got: " << k << std::endl;
            exit(-1);
          }
        }
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns coincidence matrix in csr format. That string can be used to initialize
       * a SparseMatrix (with constructor in Python). Duplicating nnzpr at the head of 
       * each row so that the format is compatible with SM csr. To make this string
       * compatible with SM fromCSR, we need to add the byte size of the string right
       * after the format tag.
       *
       * NOTE: slow, because resorts the non-zeros on each row to be compatible with SM.
       */
      inline std::string get_cm() const
      {
        std::stringstream cm_stream1, cm_stream2;

        cm_stream1 << "sm_csr_1.5 ";
        cm_stream2 << nrows << ' '
                   << ncols << ' '
                   << ind_nz.size() << ' ';

        for (size_type i = 0; i != nrows; ++i) {
          cm_stream2 << nnzpr << ' ';
          std::vector<IndNZ> buffer(nnzpr);
          std::copy(row_begin(i), row_begin(i) + nnzpr, buffer.begin());
          std::sort(buffer.begin(), buffer.end(), less_1st<size_type, value_type>());
          for (size_type j = 0; j != nnzpr; ++j) 
            cm_stream2 << buffer[j].first << ' ' << buffer[j].second << ' ';
        }
        
        cm_stream1 << cm_stream2.str().size() << ' ' << cm_stream2.str();
        return cm_stream1.str();
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns coincidence matrix in csr format, but only the non-zeros which have 
       * a bit count greater than histogram_threshold. 
       */
      inline std::string get_truncated_cm() const
      {
        std::stringstream cm_stream1, cm_stream2;

        cm_stream1 << "sm_csr_1.5 ";
        cm_stream2 << nrows << ' '
                   << ncols << ' '
                   << ind_nz.size() << ' ';

        for (size_type i = 0; i != nrows; ++i) {
          cm_stream2 << ub[i] << ' ';
          std::vector<IndNZ> buffer(nnzpr);
          std::copy(row_begin(i), row_begin(i) + ub[i], buffer.begin());
          std::sort(buffer.begin(), buffer.begin() + ub[i], 
                    less_1st<size_type, value_type>());
          for (size_type j = 0; j != ub[i]; ++j) 
            cm_stream2 << buffer[j].first << ' ' << buffer[j].second << ' ';
        }
        
        cm_stream1 << cm_stream2.str().size() << ' ' << cm_stream2.str();
        return cm_stream1.str();
      }

      //--------------------------------------------------------------------------------
      /**
       * Return a single row of the coincidence matrix, as a dense vector.
       * First requested for inspectors.
       */
      template <typename It>
      inline void get_cm_row_dense(size_type row, It begin, It end) const
      {
        {
          NTA_ASSERT(row < nrows);
        }

        std::fill(begin, end, 0);

        for (size_type i = 0; i != nnzpr; ++i) 
          *(begin + ind_nz[row*nnzpr + i].first) = ind_nz[row*nnzpr + i].second;
      }

      //--------------------------------------------------------------------------------
      template <typename It1, typename It2>
      inline void get_cm_row_sparse(size_type row, It1 begin_ind, It2 begin_nz) const
      {
        {
          NTA_ASSERT(row < nrows);
        }
        
        std::vector<IndNZ> buffer(nnzpr);
        std::copy(row_begin(row), row_begin(row) + nnzpr, buffer.begin());
        std::sort(buffer.begin(), buffer.begin() + nnzpr, 
                  less_1st<size_type, value_type>());
        for (size_type j = 0; j != nnzpr; ++j) {
          *begin_ind++ = buffer[j].first;
          *begin_nz++ = buffer[j].second;
        }
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns the amount of overlap (the number of matching bits) between x and 
       * each coincidence.
       * First requested for inspectors.
       *
       * Call in inference (matches only the _learnt_ bits of the coincidences).
       */
      template <typename It1, typename It2, typename It3>
      inline size_type overlaps(It1 x, It2 y2, It3 y3) 
      {
        size_type n = 0;
        
        for (size_type i = 0; i != nrows; ++i) {

          if (y2[i] > 0) {
            
            value_type s = 0.0f;
            size_type *p = &ind_nz[i * nnzpr].first, *p_end = p + 2 * ub[i];
            
            for (; p != p_end; p += 2)
              s += x[*p];
            
            *y3++ = s;
            ++n;
          }
        }
        
        return n;
      }

      //--------------------------------------------------------------------------------
      /**
       * The update() method maintains the counts of the on bits of each coincidence, if 
       * learning is turned on: the bits that match with the inputs more are reinforced
       * and the others are gradually ignored. The update() method has 3 parts.
       * 
       * This method takes in a vector of the indices of the active coincidences, and 
       * the input vector (needed to compute the overlap with each coincidence and 
       * increment the bit counters accordingly).
       * 
       * 1. Increment coincidence bit counts:
       * ===================================
       * For the active coincidences only, we increment the counts of the bits that match
       * between the coincidence and x. This will increase the likelihood that "useful"
       * bits get promoted for each coincidence, while the bits that don't match enough
       * will be made irrelevant. For the purpose of incrementing the counts, we need to 
       * consider _all_ the non-zeros of each active coincidence, not only the non-zeros 
       * up to ub[i], since we want the set of "important" bits to be dynamic: new 
       * "important" bits can enter the set at any point, depending on the statistics
       * of the inputs.
       *
       * 3. Normalize, infrequently:
       * ==========================
       * Once in a while, we normalize, which has the effect of pushing some coincidence
       * bits below the threshold, making them irrelevant for further inferences. This 
       * operations is done only infrequently because it takes too much time to be done
       * on each input vector. It can be thought of as an "inhibition", the more 
       * relevant bits "inhibiting" those that don't match the inputs often enough. The 
       * whole row is normalized, including the bits that are 'less relevant' (after 
       * ub[i]). We normalize *ALL* rows, so that we also normalize rows that were
       * updated in between the points at which we normalize (we normalize only every
       * 10 steps, for example, but we we update rows on each iteration).
       *
       * 2. Segregate nz above/below threshold:
       * =====================================
       * We update ub[i] for each active row i by sorting the whole row
       * and then finding the new ub[i]. Non-zeros with a count above threshold are 
       * stored before ub[i], and the others after. Note that to segregate correctly,
       * we need to take into account both the non-zeros that are currently *above* 
       * and *below* threshold: depending on the statistics of the input, those two
       * sets can change from iteration to iteration. Which means we need to sort 
       * and threshold on each iteration, *AFTER* incrementing the counts and normalizing
       * them.
       *
       * Parameters:
       * ==========
       * - active..active_end: a vector containing the indices of the active 
       *                       coincidences (size <= nrows)
       * - x..x_end: the input vector (size == ncols)
       *
       * TODO: maintain ub[i] incrementally instead of sorting each time
       * TODO: update only infrequently, and accumulate in the meantime
       * TODO: see if it's faster to normalize only the active rows, on each iteration
       * TODO: jump by 2 in 1. to avoid dereferencing the pair
       */
    private:
      template <typename It1, typename It2>
      inline void update(It1 active, It1 active_end, It2 x, It2 x_end)
      {
        { // Pre-conditions
          NTA_ASSERT(active <= active_end);
          NTA_ASSERT((size_type)(x_end - x) == ncols);
          NTA_ASSERT(0 < normalization_freq);
          NTA_ASSERT(0 < histogram_threshold);
          NTA_ASSERT(ub.size() == nrows);
          NTA_ASSERT(!ind_nz.empty() && ind_nz.size() == nrows * nnzpr);
          for (size_type i = 0; i != ind_nz.size(); ++i) 
            NTA_ASSERT(ind_nz[i].first < ncols);
          for (It1 it = active; it != active_end; ++it) 
            NTA_ASSERT(*it < nrows);
        } // End pre-conditions

        // 1. Increment the counts up to nnzpr
        for (It1 it = active; it != active_end; ++it) {

          size_type i = (size_type) *it;
          IndNZ *p_beg = row_begin(i), *p_end = p_beg + nnzpr;

          for (IndNZ* p = p_beg; p != p_end; ++p)
            p->second += x[p->first];
        }

        // 2. Normalize, infrequently
        if (iter % normalization_freq == 0) {

          normalize();

          // 3. Segregate nz above/below threshold (update ub[i])
          for (size_type i = 0; i != nrows; ++i) {

            size_type j = 0;
            IndNZ *p_beg = row_begin(i), *p_end = p_beg + nnzpr;

            std::sort(p_beg, p_end, greater_2nd<size_type, value_type>());

            while (j < nnzpr && p_beg[j].second > histogram_threshold) 
              ++j;

            ub[i] = j;
          }
        }

        { // Post-conditions
          //for (It1 it = active; it != active_end; ++it) 
          //  NTA_ASSERT(ub[*it] <= nnzpr);
        } // End post-conditions
      }

      //--------------------------------------------------------------------------------
      /**
       * The infer() method takes input vectors and produces output vectors that best
       * "represent" the input w.r.t. to the matrix of coincidences. The input, output 
       * and coincidences are all sparse binary (0/1) vectors. The non-zeros of the output
       * correspond to the coincidences that best match the input vector. The output 
       * always has constant sparsity (constant number of non-zeros = output_nnz),
       * according to FDR principles. The infer method has 2 parts, and optionally 
       * calls update() to update the coincidences (if learning is on).
       *
       * This method takes in the input vector x and produces the result vector y which
       * the output of the SP itself. The input is a binary 0/1 vector of size ncols 
       * (the size of the coincidences), and the output is another binary 0/1 vector,
       * of size nrows (the number of coincidences).
       * 
       * 1. Compute matches:
       * ==================
       * This step computes the number of overlapping bits between the input and each 
       * coincidence. This is achieved as follows:
       * Multiply current sparse matrix (in ind_nz) by x on the right, place result into
       * y. When doing that multiplication, for row i, we multiply up to ub[i] non-zeros
       * only: if we are not doing learning, ub[i] == nnzpr (set in constructor) ; if we are
       * learning, ub[i] gets adjusted in update() to the number of non-zeros whose values
       * are > threshold. The order of the non-zeros doesn't matter here, except maybe to
       * optimize cache usage (try sorting them in increasing order before ub[i]). While
       * performing the right vec prod, we also count the number of matches that are 
       * greater than stimulus_threshold (n_gt). 
       *
       * 2. Impose constant sparsity on outputs:
       * ======================================
       * This step selects the top_n coincidences that best match x (highest number of 
       * overlapping bits), sets the corresponding bits of y to 1, and the others to
       * 0 (inhibition). Before we set the bits of y to 0/1, we trigger learning with 
       * y's top_n first elements containing the indices of the non-zeros we will set
       * in y, if doLearn is true. Finally, in_place_sparse_to_dense_01 expands y in
       * place, from a vector of top_n indices to a binary 0/1 vector having 1's at 
       * the positions of the top_n indices only, and 0's elsewhere.
       *
       * Parameters:
       * ==========
       * - babyIdx: index of the baby that should compute on this call
       * - x..x_end: input vector (input to the SP)
       * - y..y_end: output vector (output of the SP)
       * - doLearn: whether to learn or not
       * - doInfer: whether to do inference or not
       * 
       * IMPLEMENTATION NOTES:
       * 1. If less than stimulus_threshold bits on in x, no coincidence
       * will match properly, so we can return the null vector right
       * away.
       *
       * 2. We use n_gt with two different meanings in this function: first,
       * it counts the number of on bits in x. Then we reuse it to mean the 
       * number of coincidences that match x above stimulus_threshold.
       *
       * 3. To compute the right vec prod (that computes the overlap between the 
       * coincidences and the input vector) in 1. (hotspot), the loop "jumps over"
       * by increments of two, because the coincidences are stored as vector of 
       * pair(index,counter value), and we need only the indices here. This is much
       * faster than iterating on each pair, and dereferencing with pair.first.
       *
       * TODO: measure impact of sorted non-zeros before ub[i] on cache
       * TODO: return only the indices of the non-zeros in the output, once 
       * integrated with the FDR TP
       * TODO: write faster asm count_non_zeros (the current one uses count_gt)
       * TODO: avoid having to resort for in_place_sparse_to_dense_01 (requires
       * writing another in_place_sparse_to_dense_01)
       */
    public:
      template <typename It1, typename It2>
      inline void compute(size_type babyIdx,
                          It1 x, It1 x_end, It2 y, It2 y_end, 
                          bool doLearn =false, bool doInfer =true)
      {
        { // Pre-conditions
          NTA_ASSERT(babyIdx < nbabies);
          NTA_ASSERT((size_type)(x_end - x) == ncols);
          NTA_ASSERT((size_type)(y_end - y) == nrows);
          NTA_ASSERT(!ind_nz.empty() && ind_nz.size() == nrows * nnzpr);
          NTA_ASSERT(ub.size() == nrows);
          for (size_type i = 0; i != ub.size(); ++i)
            NTA_ASSERT(ub[i] <= nnzpr);
          for (size_type i = 0; i != ind_nz.size(); ++i) 
            NTA_ASSERT(ind_nz[i].first < ncols);
        } // End pre-conditions

        // 0. Compute number of on bits in input vector x
        size_type n_gt = count_non_zeros(x, x_end);

        if (n_gt <= stimulus_threshold) {
          std::fill(y, y_end, 0);
          return;
        }

        // 1. Compute matches
        n_gt = 0;

        for (size_type i = 0; i != nrows; ++i) {

          // *** HOTSPOT *** in r26326
          value_type s = 0.0f;
          size_type *p = &ind_nz[i * nnzpr].first, *p_end = p + 2 * ub[i];

          for (; p != p_end; p += 2)
            s += x[*p];

          y[i] = s;
        }

        if (hysteresis > 1.0f) {
          size_type *i = &prev_winners[0], *i_end = i + n_prev_winners;
          for (; i != i_end; ++i)
            y[*i] *= hysteresis;
        }

        for (size_type i = 0; i != nrows; ++i) 
          if (y[i] > stimulus_threshold)
            ++n_gt;

        // Only for inspectors, slow, off by default
        if (!d_output.empty())
          std::copy(y, y_end, d_output[babyIdx].begin());

        // 2. Impose constant output sparsity
        size_type top_n = std::min(output_nnz, n_gt);

        if (top_n == 0) {
          std::fill(y, y_end, 0);
          return;
        }

        partial_argsort(top_n, y, y_end, y, y_end);

        if (doLearn)
          update(y, y + top_n, x, x_end);

        if (hysteresis > 1.0f) {
          n_prev_winners = top_n;
          std::copy(y, y + top_n, prev_winners.begin());
        }

        // TODO: disconnect this if doInfer is false
        // in_place_sparse_to_dense_01 requires sorted indices!
        std::sort(y, y + top_n);
        in_place_sparse_to_dense_01(top_n, y, y_end);
     
        ++iter;
      }

      //--------------------------------------------------------------------------------
      // PERSISTENCE
      //--------------------------------------------------------------------------------
      /**
       * This methods to pickle/unpickle a FDRSpatial. 
       */
      inline size_type persistent_size() const
      {
        std::stringstream buff;
        save(buff);
        return buff.str().size();
      }

      //--------------------------------------------------------------------------------
      inline void save(std::ostream& out_stream) const
      {
        {
          NTA_ASSERT(out_stream.good());
          NTA_ASSERT(ind_nz.size() == nrows * nnzpr);
          NTA_ASSERT(ub.size() == nRows());
          for (size_type i = 0; i != ind_nz.size(); ++i) 
            NTA_ASSERT(ind_nz[i].first < ncols);
        }

        out_stream << version() << ' ' << nbabies << ' '
                   << nrows << ' ' << ncols << ' ' << nnzpr << ' '
                   << iter << ' '
                   << output_nnz << ' '
                   << hysteresis << ' '
                   << stimulus_threshold << ' '
                   << histogram_threshold << ' '
                   << normalization_sum << ' '
                   << normalization_freq << ' '
                   << ub << ' '
                   << ind_nz << ' '
                   << n_prev_winners << ' '
                   << prev_winners << ' ';
      }

      //--------------------------------------------------------------------------------
      inline void load(std::istream& in_stream)
      {
        {
          NTA_ASSERT(in_stream.good());
        }
        
        std::string ver;
        in_stream >> ver;
        assert(ver == version());

        in_stream >> nbabies 
                  >> nrows >> ncols >> nnzpr >> iter
                  >> output_nnz
                  >> hysteresis
                  >> stimulus_threshold
                  >> histogram_threshold
                  >> normalization_sum
                  >> normalization_freq
                  >> ub
                  >> ind_nz
                  >> n_prev_winners
                  >> prev_winners;

        d_output.resize(0);

        {
          NTA_ASSERT(ind_nz.size() == nrows * nnzpr);
          NTA_ASSERT(1.0 <= hysteresis);
          NTA_ASSERT(0 < histogram_threshold);
          NTA_ASSERT(0 < normalization_sum);
          NTA_ASSERT(0 < normalization_freq);
          NTA_ASSERT(ub.size() == nRows());
          for (size_type i = 0; i != ub.size(); ++i)
            NTA_ASSERT(ub[i] <= nnzpr);
          for (size_type i = 0; i != ind_nz.size(); ++i) 
            NTA_ASSERT(ind_nz[i].first < ncols);
        }
      }

    private:

      //--------------------------------------------------------------------------------
      /**
       * Returns a pointer to the first (index,value) pair of row i.
       */
      inline IndNZ* row_begin(size_type i) 
      { 
        NTA_ASSERT(i < nRows());
        return &ind_nz[0] + i * nnzpr; 
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns a pointer to the first (index,value) pair of row i.
       */
      inline const IndNZ* row_begin(size_type i) const 
      { 
        NTA_ASSERT(i < nRows());
        return &ind_nz[0] + i * nnzpr; 
      }

      //--------------------------------------------------------------------------------
      /**
       * Normalizes each row of the coincidence matrix separately, so that the sum
       * of each column is equal to normalization_sum (set in constructor).
       */
      inline void normalize()
      {
        NTA_ASSERT(0 < normalization_sum);

        for (size_type i = 0; i != nrows; ++i) {
          IndNZ* p_beg = row_begin(i), *p_end = p_beg + nnzpr;
          value_type s = 0.0f;
          for (IndNZ* p = p_beg; p != p_end; ++p)
            s += p->second;
          if (s == 0.0f)
            return;
          value_type k = normalization_sum / s;
          NTA_ASSERT(k != 0.0f);
          for (IndNZ* p = p_beg; p != p_end; ++p)
            p->second *= k;
        }
      }

      //--------------------------------------------------------------------------------
      size_type nbabies;
      size_type nrows, ncols, nnzpr;  // nnzpr = number of non-zeros per row
      size_type iter;                 // current iteration number
      size_type output_nnz;           // number of nz desired in output vector
      value_type hysteresis;          // hysteresis factor
      value_type stimulus_threshold;  // see infer()
      value_type histogram_threshold; // see update()
      value_type normalization_sum;   // see update()
      size_type normalization_freq;   // see update()

      std::vector<size_type> ub;   // ub[row] = 1+index of last nz > histogram_threshold
      std::vector<IndNZ> ind_nz;   // vectors of pairs <index,bit count>

      size_type n_prev_winners;            // for hysteresis, n of prev winners
      std::vector<size_type> prev_winners; // for hysteresis

      // for inspectors only, makes compute slow
      std::vector<std::vector<value_type> > d_output;
    };

    //--------------------------------------------------------------------------------
  } // end namespace algorithms
} // end namespace nta

#endif // NTA_FDR_SPATIAL_HPP
