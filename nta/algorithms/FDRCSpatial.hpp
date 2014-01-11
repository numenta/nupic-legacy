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

#ifndef NTA_FDR_C_SPATIAL_HPP
#define NTA_FDR_C_SPATIAL_HPP

#include <nta/math/stl_io.hpp>

#ifdef NTA_PLATFORM_linux64
#define P_INC 4
#else
#define P_INC 2
#endif

namespace nta {
  namespace algorithms {

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
     */

    //--------------------------------------------------------------------------------
    /*
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
    class Inhibition
    {
    public:
      typedef nta::UInt32 size_type;
      typedef nta::Real32 value_type;

    private:
      size_type small;
      size_type c_height, c_width, c_field_size;
      size_type inhibition_radius;
      std::vector<std::vector<size_type> > inhibition_area;

    public:
      //--------------------------------------------------------------------------------
      inline Inhibition(size_type _c_height =0, size_type _c_width =0,
                        value_type _desired_density =1.0f,
                        size_type _small =0)
      {
        initialize(_c_height, _c_width, _desired_density, _small);
      }

      //--------------------------------------------------------------------------------
      inline void initialize(size_type _c_height =0, size_type _c_width =0,
                             value_type _desired_density =1.0f,
                             size_type _small =0)
      {
        small = _small;
        c_height = _c_height;
        c_width = _c_width;
        c_field_size = c_height * c_width;
        inhibition_radius = size_type(sqrt(1.0f/_desired_density) - 1.0f);

        if (estimate_max_size_bytes() > 600*1024*1024)
          small = 1;

        if (small == 1) {
          inhibition_area.resize(0);
          return;
        }

        inhibition_area.resize(c_field_size);

        for (size_type c = 0; c != c_field_size; ++c) {

          // so that we can reinitialize, for example when
          // we change the desired density
          inhibition_area[c].resize(0);

          int ch = c / c_width;
          int cw = c % c_width;
          int lb_height = std::max((int) 0, ch - (int) inhibition_radius);
          int ub_height = std::min(ch + inhibition_radius + 1, c_height);
          int lb_width = std::max((int) 0, cw - (int) inhibition_radius);
          int ub_width = std::min(cw + inhibition_radius + 1, c_width);

          for (int py = lb_height; py != ub_height; ++py) {
            for (int px = lb_width; px != ub_width; ++px) {
              int w = px + c_width * py;
              if (w != (int) c)
                inhibition_area[c].push_back(w);
            }
          }
        }
      }

      //--------------------------------------------------------------------------------
      inline int getSmall() const { return small; }
      inline size_type getInhibitionRadius() const { return inhibition_radius; }
      inline size_type getHeight() const { return c_height; }
      inline size_type getWidth() const { return c_width; }
      inline size_type n_bytes() const { return nta::n_bytes(inhibition_area); }

      //--------------------------------------------------------------------------------
      inline size_type estimate_max_size_bytes() const
      {
        size_type a = 0;

        for (size_type c = 0; c != c_field_size; ++c) {

          int ch = c / c_width;
          int cw = c % c_width;
          int lb_height = std::max((int) 0, ch - (int) inhibition_radius);
          int ub_height = std::min(ch + inhibition_radius + 1, c_height);
          int lb_width = std::max((int) 0, cw - (int) inhibition_radius);
          int ub_width = std::min(cw + inhibition_radius + 1, c_width);

          a += (ub_height - lb_height) * (ub_width - lb_width);
        }

        return a * sizeof(int);
      }

      //--------------------------------------------------------------------------------
      inline void setDesiredOutputDensity(value_type v)
      {
        initialize(c_height, c_width, v, small);
      }

      //--------------------------------------------------------------------------------
      /*
       * TODO: precompute deltas on which to compute the max, or
       * sometimes compute on a whole square if max was in the delta
       * removed. This retests the same pixels over and over again.
       * Don't forget that there are deltas added and deltas removed.
       * Maybe store the indices of the columns in inhibition radius
       * as well as the deltas.
       * TODO: as soon as greater value than y[c] / .95 found in the new
       * delta, cell is inhibited
       */
      template <typename It1, typename It2>
      inline size_type compute(It1 x, It2 y, size_type stimulus_threshold =0,
                               value_type k =.95f)
      {
        size_type n_active = 0;

        if (small == 0) {

          for (size_type c = 0; c != c_field_size; ++c) {

            if (x[c] <= stimulus_threshold)
              continue;

            value_type val_c = x[c] / k;
            size_type* w = &inhibition_area[c][0];
            size_type* w_end = w + inhibition_area[c].size();

            while (w != w_end && val_c > x[*w])
              ++w;

            if (w == w_end)
              y[n_active++] = c;
          }

        } else if (small == 1) {

          for (size_type c = 0; c != c_field_size; ++c) {

            if (x[c] <= stimulus_threshold)
              continue;

            value_type val_c = x[c] / k;

            int ch = c / c_width;
            int cw = c % c_width;
            int lb_height = std::max((int) 0, ch - (int) inhibition_radius);
            int ub_height = std::min(ch + inhibition_radius + 1, c_height);
            int lb_width = std::max((int) 0, cw - (int) inhibition_radius);
            int ub_width = std::min(cw + inhibition_radius + 1, c_width);

            bool stop = false;

            for (int px = lb_width; px != ub_width && !stop; ++px) {
              for (int py = lb_height; py != ub_height && !stop; ++py) {
                size_type w = (size_type) px + c_width * (size_type) py;
                if (w == c)
                  continue;
                stop = val_c <= x[w];
              }
            }

            if (!stop)
              y[n_active++] = c;
          }
        }

        return n_active;
      }
    };

    //--------------------------------------------------------------------------------
    // used for the old-fashioned sort in Inhibition2::compute()
    //
    // We would put this inside the function, but gcc 4.5 busts us.
    // A language lawyer explains that C++98/03 (the current one) does
    // not allow instantiation of a template with a local type.
    template <typename It>
    struct CMySort
    {
      typedef nta::UInt32 size_type;
      It _x;
      CMySort(It& x) : _x(x) {}
      bool operator()(size_type A, size_type B) const {
        return _x[A] > _x[B];
      }
    };

    //--------------------------------------------------------------------------------
    //--------------------------------------------------------------------------------
    /*
     * This class implements cell inhibition. Given a region of cells and their
     * firing strengths, it returns the list of indices of the cells that are
     * firing after inhibition.
     *
     * Inhibition is computed per "inhibition area" within the layer. The
     * size of the inhibition area is controlled by the '_inhibition_radius'
     * construction parameter. An inhibition area is a square section of cells
     * with a width and height of (_inhibition_radius * 2 + 1).
     *
     * A cell is only allowed to fire if it is among the top N% strongest cells
     * within the inhibition area centered around itself, where N is given by the
     * construction parameter '_local_area_density'.
     *
     */
    class Inhibition2
    {
    public:
      typedef nta::UInt32 size_type;
      typedef nta::Real32 value_type;

    private:
      size_type c_height, c_width, c_field_size;
      size_type inhibition_radius;
      value_type local_area_density;

    public:
      //--------------------------------------------------------------------------------
      // Parameters:
      //    _c_height:          height of the region, in cells
      //    _c_width:           width of the region, in cells
      //    _inhibition_radius: inhibition radius, in cells
      //    _local_area_density: desired local area density within each
      //                            inhibition area.
      //
      inline Inhibition2(size_type _c_height =0, size_type _c_width =0,
                         size_type _inhibition_radius =10,
                         value_type _local_area_density =0.02f)
      {
        initialize(_c_height, _c_width, _inhibition_radius, _local_area_density);
      }

      //--------------------------------------------------------------------------------
      // Parameters:
      //    _c_height:          height of the region, in cells
      //    _c_width:           width of the region, in cells
      //    _inhibition_radius: inhibition radius, in cells
      //    _local_area_density: desired local area density within each
      //                            inhibition area.
      //
      inline void initialize(size_type _c_height =0, size_type _c_width =0,
                             size_type _inhibition_radius =10,
                             value_type _local_area_density =0.02f)
      {
        NTA_ASSERT(0 < _local_area_density && _local_area_density <= 1);

        c_height = _c_height;
        c_width = _c_width;
        c_field_size = c_height * c_width;
        inhibition_radius = _inhibition_radius;
        local_area_density = _local_area_density;
      }

      //--------------------------------------------------------------------------------
      // Various getter methods
      inline size_type getInhibitionRadius() const { return inhibition_radius; }
      inline value_type getLocalAreaDensity() const { return local_area_density; }
      inline size_type getHeight() const { return c_height; }
      inline size_type getWidth() const { return c_width; }

      //--------------------------------------------------------------------------------
      // Modify the desired local area density.
      inline void setDesiredOutputDensity(value_type v)
      {
        initialize(c_height, c_width, inhibition_radius, v);
      }

      //--------------------------------------------------------------------------------
      // Compute which cells are firing after inhibition. On return,
      //  the y array will be filled in with the cell indices of the cells that are
      //  firing after inhibition. The number of firing cells placed into the
      //  y array is given by the return value.
      //
      // Parameters:
      //    x:                    array of cell firing strengths
      //    y:                    space to hold output cell indices
      //    stimulus_threshold:   Any cell with an overlap of less than
      //                            stimulusThreshold is not allowed to win
      //    add_to_winners:       Typically a very small number (like .00001)
      //                            that gets added to the firing strength
      //                            of each cell that wins as we go along. This
      //                            prevents us from returning more than the
      //                            desired density of cells when many cells
      //                            are firing with the exact same strength.
      template <typename It1, typename It2>
      inline size_type compute(It1 x, It2 y, value_type stimulus_threshold =0,
              value_type add_to_winners =0)
      {
        // This holds the total number of active cells firing after inhibition
        size_type n_active = 0;

        if (inhibition_radius >= c_field_size - 1) {  // optimized special case
          static std::vector<size_type> vectIndices;
          vectIndices.clear();              // purge residual data

          // get the columns with non-trivial values
          for (size_type c = 0; c != c_field_size; ++c) {
            if (x[c] >= stimulus_threshold)
              vectIndices.push_back(c);
          }

          // sort the qualified columns in descending value order
#if 0
          // the lambda sort function requires -std=c++0x or -std=gnu++0x,
          // first supported in gnu 4.5, but our usage here busts in 4.5.2
          // and may first work in 4.6, not yet available pre-packaged for
          // Ubuntu 11.04.
          std::sort(vectIndices.begin(), vectIndices.end(), []( size_type a, size_type b) { return x[a] > x[b] ; }) ;
#else
          // sort the old-fashioned way
          CMySort<It1> s(x);
          std::sort(vectIndices.begin(), vectIndices.end(), s);
#endif

          // compute how many columns we want
          size_type top_n = size_type(0.5 + local_area_density * c_field_size);
          if (top_n == 0)
            top_n = 1;

          // select the top_n biggest values, less if there aren't enough
          if (vectIndices.size() > top_n)
            vectIndices.resize(top_n);
          std::sort(vectIndices.begin(), vectIndices.end()); // must the returned indices be sorted?
          while (n_active < vectIndices.size()) {
            y[n_active] = vectIndices[n_active];
            n_active++;
          }

        }  // optimized special case
        else {

          // ------------------------------------------------------------------
          // For every cell in this region....
          for (size_type c = 0; c != c_field_size; ++c) {

            // If the firing strength of this cell is below stimulus threshold,
            //  it's not allowed to fire
            if (x[c] < stimulus_threshold)
              continue;


            // ------------------------------------------------------------------
            // Get the bounds of the inhibition area around this cell
            int ch = c / c_width;   // The column index of this cell
            int cw = c % c_width;   // The row index of this cell

            // the index of top of the inhibition area
            int lb_height = std::max((int) 0, ch - (int) inhibition_radius);

            // the index of bottom of the inhibition area
            int ub_height = std::min(ch + inhibition_radius + 1, c_height);

            // the index of left side of the inhibition area
            int lb_width = std::max((int) 0, cw - (int) inhibition_radius);

            // the index of right side of the inhibition area
            int ub_width = std::min(cw + inhibition_radius + 1, c_width);


            // ----------------------------------------------------------------
            // How many cells are allowed to be on within this inhibition area?
            // Put that into top_n
            size_type top_n =
              (size_type) (0.5 + local_area_density
                           * (ub_height - lb_height) * (ub_width - lb_width));
            if (top_n == 0)
              top_n = 1;


            // ----------------------------------------------------------------
            // Iterate over all other cells within this inhibition area. Keep a count
            //  of how many are firing STRONGER than this cell. This count goes
            //  into k.
            int k = 0;
            for (int px = lb_width; px != ub_width && k < (int) top_n; ++px)
              for (int py = lb_height; py != ub_height && k < (int) top_n; ++py)
                if (x[(size_type)px + c_width * (size_type)py] > x[c])
                  ++k;


            // ----------------------------------------------------------------
            // If this cell is within the top_n strongest cells, then it is allowed
            //  to fire.
            //
            // Take a note of the following example scenario to explain why we need
            // add_to_winners:
            //   1.) top_n is 10
            //   2.) there are 20 cells in the inhibition area all firing with
            //        strength 0.8,  all other cells are firing less than 0.8
            //   3.) the current cell is firing with strength 0.8.
            //
            // In this scenario, k will be 0 because no other cells are firing
            //  stronger than the current cell and we will decide to fire this
            //  cell. Likewise, for each of the other 20 cells, they will also
            //  calculate a k of 0 and will also decide to fire. In the end, we
            //  will end up with 20 firing cells, when the user wanted only 10.
            //
            // To address this, we add a small factor to each cell's firing strength
            //  when we decide to fire it. In this way, the first 10 cells that
            //  we scan with strength 0.8 will get boosted to strength
            //  0.8+add_to_winners, and the next 10 will NOT fire because their
            //  k will be > 10.
            //
            if (k < (int) top_n) {
              y[n_active++] = c;
              // add_to_winners prevents us from choosing more than top_n winners
              //  per inhibition region when more than top_n all have the same
              //  highest score.
              x[c] += add_to_winners;
            }
          }  // for every cell in this region
        }  // if not the optimized special case
        return n_active;
      }
    };

    //--------------------------------------------------------------------------------
    //--------------------------------------------------------------------------------
    class FDRCSpatial
    {
    public:
      typedef nta::UInt32 size_type;
      typedef nta::Real32 value_type;
      typedef std::pair<size_type, value_type*> IndNZ;

    public:
      //--------------------------------------------------------------------------------
      /**
       * Constructor for SP.
       *
       * Creates a random sparse matrix with uniformly distributed non-zeros, all the
       * non-zeros having value 1, unless _clone is true, in which case the coincidence
       * matrix is not set here, but can be set later from a SM with set_cm.
       * The coincidences are sparse 0/1 vectors (vertices of the unit hypercube of
       * dimension input_width).
       *
       * Parameters:
       * ==========
       * - nbabies: the number of babies in this FDR SP
       * _ c_height, c_width: the shape of the coincidence array
       * - nrows: the number of coincidence vectors
       * - input_width: the size of each coincidence vector (number of elements)
       * - nnzpr: number of non-zeros per row, i.e. number of non-zeros in each
       *          binary coincidence
       * - density: number of non-zeros in result vector for infer() ( <= nrows)
       * - stimulus_threshold: minimum number of bits in the input that need to
       *          match with one coincidence for the input vector. If that threshold
       *          is not met by a pair (coincidence,input), the output for that
       *          coincidence is zero
       * - sparsity_algo: which sparsity enforcing algo to use: globalMax or cellSweeper
       * - desired_density: how many non-zeros should each output contain
       * - clone: whether to clone this spatial pooler or not. Two or more spatial
       *          poolers that are cloned share the same coincidences.
       * - coincidence_type: the type of coincidence to use. The type determines
       *          the distribution of the non-zeros inside the coincidence.
       *          Available types: uniform, gaussian. If gaussian, specify rf_x
       *          and sigma.
       * - rf_x:  length of the receptive field in each coincidence in gaussian
       *          mode: > 0, input_width % rf_x == 0.
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
      FDRCSpatial(size_type _input_height, size_type _input_width,
                  size_type _c_height, size_type _c_width,
                  size_type _c_rf_radius, size_type _c_pool_size, size_type _c_nnz,
                  value_type _desired_density_learning =.1f,
                  value_type _desired_density_inference =.1f,
                  size_type _stimulus_threshold_learning =0,
                  size_type _stimulus_threshold_inference =1,
                  value_type _convolution_k_learning =.95f,
                  value_type _convolution_k_inference =.95f,
                  int _seed =-1,
                  value_type _threshold_cte =800.0f,
                  value_type _normalization_sum =1000.0f,
                  size_type _clone_height =0, size_type _clone_width =0,
                  size_type small_threshold_bytes =600*1024*1024) // MB
        : rng(_seed == -1 ? rand() : _seed),
          input_size(_input_height * _input_width),
          input_height(_input_height), input_width(_input_width),
          c_height(_c_height), c_width(_c_width),
          c_field_size(_c_height * _c_width),
          c_rf_radius(_c_rf_radius),
          c_pool_size(_c_pool_size),
          c_nnz(_c_nnz),
          c_rf_side(2*c_rf_radius+1),
          c_rf_size(c_rf_side * c_rf_side),
          n_masters(_clone_height > 0 ? _clone_height * _clone_width : c_field_size),
          clone_height(_clone_height), clone_width(_clone_width),
          desired_density_learning(_desired_density_learning),
          desired_density_inference(_desired_density_inference),
          stimulus_threshold_learning(_stimulus_threshold_learning),
          stimulus_threshold_inference(_stimulus_threshold_inference),
          convolution_k_learning(_convolution_k_learning),
          convolution_k_inference(_convolution_k_inference),
          histogram_threshold((value_type) _threshold_cte / (value_type) _c_nnz),
          normalization_sum(_normalization_sum),
          n_active(0),
          small(isCloned() && estimate_max_size_bytes() > small_threshold_bytes),
          ind_nz(0),
          hists(n_masters * c_pool_size),
          cl_map(0),
          inv_cl_map(0),
          int_buffer(std::max(c_rf_size, c_field_size), 0),
          d_output(0),
          inhibition(c_height, c_width, desired_density_learning),
          yy(getNColumns(), 0),
          t_ind()
      {
        { // Pre-conditions
          NTA_ASSERT(!(isCloned() == false && small == true));
          NTA_ASSERT((clone_height == 0 && clone_width == 0)
                     || clone_height * clone_width != 0);
          NTA_ASSERT(c_nnz <= c_pool_size);
          NTA_ASSERT(c_pool_size <= (2 * c_rf_radius + 1) * (2 * c_rf_radius + 1));
          NTA_ASSERT(0 < histogram_threshold);
          NTA_ASSERT(0 < normalization_sum);
        } // End pre-conditions

        initialize_cl_maps();
        initialize_rfs();
        initialize_ind_nz(); // needs rfs and cl_maps
        add_val(hists.begin(), hists.end(), 100);
        normalize();

        greater_2nd_p<size_type, value_type> order;

        for (size_type i = 0; i != indNZNRows(); ++i) {
          IndNZ *beg = row_begin(i), *end = beg + c_pool_size;
          std::partial_sort(beg, beg + c_nnz, end, order);
        }

        { // Post-conditions
          NTA_ASSERT((small && ind_nz.size() == n_masters * c_pool_size)
                     || (!small && ind_nz.size() == c_field_size * c_pool_size));
        } // End post-conditions
      }

    private:
      //--------------------------------------------------------------------------------
      inline void initialize_cl_maps()
      {
        if (!isCloned())
          return;

        cl_map.resize(c_field_size);
        inv_cl_map.resize(getNMasters());

        for (size_type i = 0; i != getNMasters(); ++i)
          inv_cl_map[i].clear();

        for (size_type i = 0; i != c_field_size; ++i) {
          cl_map[i] = clone_width * ((i / c_width) % clone_height)
            + (i % c_width) % clone_width;
          inv_cl_map[cl_map[i]].push_back(i);
        }

        { // Post-conditions
          for (size_type i = 0; i != inv_cl_map.size(); ++i) {
            NTA_ASSERT(inv_cl_map[i].size() < c_field_size);
            for (size_type j = 0; j != inv_cl_map[i].size(); ++j)
              NTA_ASSERT(inv_cl_map[i][j] < c_field_size);
          }
        }
      }

      //--------------------------------------------------------------------------------
      inline void initialize_rfs()
      {
        // compute all receptive fields and store their boundaries
        // step is in float, but the rest in double to emulate what numpy
        // is doing and get an exact match with Python in unit tests.
        double start_height = c_rf_radius;
        double stop_height = (input_height - 1) - c_rf_radius + 1;
        float step_height = (stop_height - start_height) / double(c_height);
        double start_width = c_rf_radius;
        double stop_width = (input_width - 1) - c_rf_radius + 1;
        float step_width = (stop_width - start_width) / double(c_width);
        double fch = start_height;
        double fcw = start_width;

        // Could avoid storing this one, except for getMasterLearnedCoincidence,
        // used by the inspectors
        rfs.resize(4 * c_field_size);
        size_type* rfs_p = & rfs[0];
        size_type c_idx = 0;

        for (int i = 0; i != (int) c_height; ++i, fch += step_height) {
          fcw = start_width;
          for (int j = 0; j != (int) c_width; ++j, fcw += step_width, ++c_idx) {

            NTA_ASSERT(c_idx < c_field_size);

            int ch = (int) fch, cw = (int) fcw;
            *rfs_p++ = ch - c_rf_radius;
            *rfs_p++ = ch + c_rf_radius + 1;
            *rfs_p++ = cw - c_rf_radius;
            *rfs_p++ = cw + c_rf_radius + 1;
          }
        }
      }

      //--------------------------------------------------------------------------------
      inline void initialize_ind_nz(size_type* indnz =NULL)
      {
        ind_nz.resize((small ? n_masters : c_field_size) * c_pool_size);

        std::vector<size_type> m_ind, perm(c_rf_size);
        for (size_type ii = 0; ii != c_rf_size; ++ii)
          perm[ii] = ii;

        if (!indnz) { // initialization in constructor

          if (isCloned()) { // cloned initialization, in constructor

            // TODO: get rid of int_buffer?
            for (size_type i = 0; i != c_rf_size; ++i)
              int_buffer[i] = i;

            m_ind.resize(n_masters * c_pool_size);

            for (size_type i = 0; i != n_masters; ++i) {
              std::random_shuffle(perm.begin(), perm.end(), rng);
              for (size_type ii = 0; ii != c_pool_size; ++ii)
                m_ind[i*c_pool_size + ii] = int_buffer[perm[ii]];
              rand_float_range(hists, i*c_pool_size, (i+1)*c_pool_size, rng);
            }

            if (small) { // cloned and small

              size_type k = 0;
              for (size_type i = 0; i != n_masters; ++i)
                for (size_type ii = 0; ii != c_pool_size; ++ii, ++k)
                  ind_nz[k] = std::make_pair(m_ind[k], &hists[k]);

            } else { // cloned, not small

              // unroll positions of sampling bits
              // grab them here so that the calls to the rng are in the same
              // order as Python...
              size_type k = 0;
              for (size_type c = 0; c != c_field_size; ++c) {

                size_type ii_start = cl_map[c] * c_pool_size;
                size_type ii_end = ii_start + c_pool_size;

                for (size_type ii = ii_start; ii != ii_end; ++ii)
                  ind_nz[k++] = std::make_pair(from_rf(c, m_ind[ii]), &hists[ii]);
              }

            } // end clone and not small

          } else { // initialization when not cloning, in constructor

            size_type* rfs_p = &rfs[0];
            for (size_type c = 0; c != c_field_size; ++c) {

              int lb_height = *rfs_p++, ub_height = *rfs_p++;
              int lb_width = *rfs_p++, ub_width = *rfs_p++;

              size_type k = 0;
              for (int y = lb_height; y != ub_height; ++y)
                for (int x = lb_width; x != ub_width; ++x)
                  int_buffer[k++] = y * input_width + x;

              std::random_shuffle(perm.begin(), perm.end(), rng);

              size_type ii_start = c * c_pool_size;
              size_type ii_end = ii_start + c_pool_size;

              for (size_type ii = ii_start; ii != ii_end; ++ii) {
                NTA_ASSERT(ii - ii_start < perm.size());
                NTA_ASSERT(perm[ii - ii_start] < int_buffer.size());
                size_type pos_in_input = int_buffer[perm[ii - ii_start]];
                NTA_ASSERT(pos_in_input < input_size);
                ind_nz[ii] = std::make_pair(pos_in_input, &hists[ii]);
              }

              rand_float_range(hists, ii_start, ii_end, rng);
            }
          }

          return;
        } // end initialization in constructor

        //----------------------------------------
        // Initialization with indnz, in load
        //----------------------------------------

        if (isCloned()) { // cloned

          size_type k = 0;

          for (size_type c = 0; c != indNZNRows(); ++c) {

            size_type ii_start = (!small ? cl_map[c] : c) * c_pool_size;
            size_type ii_end = ii_start + c_pool_size;

            for (size_type ii = ii_start; ii != ii_end; ++ii) {
              size_type pos_in_rf = indnz[2*ii];
              size_type pos_in_input = !small ? from_rf(c, pos_in_rf) : pos_in_rf;
              value_type* ptr = &hists[0] + indnz[2*ii+1];
              ind_nz[k++] = std::make_pair(pos_in_input, ptr);
            }
          }

        } else { // initialization when not cloning, in load

          for (size_type c = 0; c != c_field_size; ++c) {

            size_type ii_start = c * c_pool_size;
            size_type ii_end = ii_start + c_pool_size;

            for (size_type ii = ii_start; ii != ii_end; ++ii)
              ind_nz[ii] = std::make_pair(indnz[2*ii], &hists[0] + indnz[2*ii+1]);
          }
        }
      }

    public:
      //--------------------------------------------------------------------------------
      /**
       * Null constructor for persistence in Python.
       */
      inline FDRCSpatial() {}

      //--------------------------------------------------------------------------------
      inline ~FDRCSpatial() {}

      //--------------------------------------------------------------------------------
      /**
       * This version tag is used in persistence.
       */
      inline const std::string version() const { return "fdrcsp_2.0"; }

      //--------------------------------------------------------------------------------
      /**
       * Various accessors.
       */
      inline bool isCloned() const { return clone_height > 0; }
      inline size_type getNMasters() const { return n_masters; }
      inline size_type getNColumns() const { return c_field_size; }
      inline size_type getInputSize() const { return input_size; }
      inline size_type getRFSide() const { return c_rf_side; }
      inline size_type getBitPoolSizePerCoincidence() const { return c_pool_size; }
      inline size_type getNSamplingBitsPerCoincidence() const { return c_nnz; }
      inline size_type getInhibitionRadius() const
      { return inhibition.getInhibitionRadius(); }
      inline size_type getStimulusThresholdForLearning() const
      { return stimulus_threshold_learning; }
      inline size_type getStimulusThresholdForInference() const
      { return stimulus_threshold_inference; }
      inline value_type getHistogramThreshold() const { return histogram_threshold; }
      inline value_type getNormalizationSum() const { return normalization_sum; }

      inline std::pair<size_type, size_type> getInputShape() const
      {
        return std::make_pair(input_height, input_width);
      }

      inline std::pair<size_type, size_type> getCoincidenceFieldShape() const
      {
        return std::make_pair(c_height, c_width);
      }

      inline std::pair<size_type, size_type> getCloningShape() const
      {
        return std::make_pair(clone_height, clone_width);
      }

      //--------------------------------------------------------------------------------
      inline size_t n_bytes() const
      {
        size_t n = 64 * sizeof(size_type);
        n += nta::n_bytes(ind_nz) + nta::n_bytes(hists);
        n += nta::n_bytes(cl_map) + nta::n_bytes(inv_cl_map);
        n += inhibition.n_bytes();
        n += nta::n_bytes(int_buffer);
        n += nta::n_bytes(d_output);
        n += nta::n_bytes(yy);
        n += nta::n_bytes(t_ind);
        n += nta::n_bytes(rfs);
        return n;
      }

      //--------------------------------------------------------------------------------
      inline bool is_small() const { return small; }

      //--------------------------------------------------------------------------------
      inline void print_size_stats(bool estimate=false) const
      {
        if (estimate) {

          cout << "Estimated" << endl;
          cout << "nc       =", c_field_size, endl;
          cout << "pool     =", c_pool_size, endl;
          cout << "ind_nz   =", (c_field_size * c_pool_size * sizeof(IndNZ)), endl;
          cout << "hists    =",(n_masters * c_pool_size * sizeof(value_type)), endl;
          cout << "maps     =", (2 * c_field_size * sizeof(size_type)), endl;
          size_type ir = inhibition.getInhibitionRadius();
          size_type m = (2*ir+1)*(2*ir+1);
          cout << "inhib    =", (c_field_size * (16 + m * sizeof(size_type))), endl;
          cout << "rfs      =", (4 * c_field_size * sizeof(size_type)), endl;

        } else {

          size_type n = 64 * sizeof(size_type);
          n += nta::n_bytes(d_output);
          n += nta::n_bytes(yy);

          cout <<
            " nc           =", c_field_size, endl,
            "pool          =", c_pool_size, endl,
            "small         =", (small ? "yes" : "no"), endl,
            "ind_nz        =", nta::n_bytes(ind_nz), endl,
            "hists         =", nta::n_bytes(hists), endl,
            "maps          =", (nta::n_bytes(cl_map) + nta::n_bytes(inv_cl_map)), endl,
            "inhib         =", inhibition.n_bytes(), endl,
            "rfs           =", nta::n_bytes(rfs), endl,
            "t_ind         =", nta::n_bytes(t_ind), endl,
            "int buffer    =", nta::n_bytes(int_buffer), endl,
            "other         =", n, endl,
            "total         =", n_bytes(), endl;
        }
      }

      //--------------------------------------------------------------------------------
      // TODO: the estimate doesn't seem to be too accurate ??
      // but IndNZ is the quadratic term that leads the asymptote
      inline size_type estimate_max_size_bytes() const
      {
        size_type n = 64 * sizeof(size_type);
        n += c_field_size * c_pool_size * sizeof(IndNZ); // ind_nz
        n += n_masters * c_pool_size * sizeof(value_type); // hists
        n += 2 * c_field_size * sizeof(size_type); // maps
        size_type ir = inhibition.getInhibitionRadius();
        size_type m = (2*ir+1)*(2*ir+1);
        n += c_field_size * (16 + m * sizeof(size_type)); // inhibition_area
        n += 4 * c_field_size * sizeof(size_type); // rfs
        n += std::max(c_rf_size, c_field_size) * sizeof(size_type); // int_buffer
        n += input_size * c_nnz * sizeof(size_type*); // t_ind
        n += input_size * sizeof(size_type);
        n += c_field_size * sizeof(size_type);
        return n;
      }

      //--------------------------------------------------------------------------------
      inline void reset() {}

      //--------------------------------------------------------------------------------
      /**
       * For inspectors.
       * This makes compute slower.
       */
      inline void setStoreDenseOutput(bool x)
      {
        d_output.resize(x * getNColumns());
      }

      //--------------------------------------------------------------------------------
      /**
       * For inspectors, only if setStoreDenseOutput(true) was called before!
       */
      template <typename It>
      inline void get_dense_output(It beg) const
      {
        NTA_ASSERT(!d_output.empty());

        for (size_type i = 0; i != getNColumns(); ++i)
          *beg++ = d_output[i];
      }

      //--------------------------------------------------------------------------------
      /**
       * Get the coincidences and histogram counts, either whole, or just the learnt
       * part.
       * For debugging and testing only, SLOW.
       * Doesn't work in nupic2.
       */
      inline SparseMatrix<UInt32, Real32>
      cm(bool withCounts =true, bool learnt =false) const
      {
        SparseMatrix<UInt32, Real32> m(c_field_size, input_size);

        for (size_type i = 0; i != c_field_size; ++i) {
          size_type beg = (small ? cl_map[i] : i) * c_pool_size;
          size_type end = learnt ? beg + c_nnz : beg + c_pool_size;
          for (size_type j = beg; j != end; ++j) {
            value_type count = withCounts ? *(ind_nz[j].second) : 1;
            size_type pos_in_input = small ? from_rf(i, ind_nz[j].first) : ind_nz[j].first;
            m.set(i, pos_in_input, count);
          }
        }

        return m;
      }

      //--------------------------------------------------------------------------------
      /*
       * Doesn't work in nupic2.
       */
      inline SparseMatrix<UInt32, Real32> cm_t() const
      {
        SparseMatrix<UInt32, Real32> m(c_field_size, input_size);

        for (size_type j = 0; j != input_size; ++j)
          for (size_type k = 0; k != t_ind[j].size(); ++k)
            m.set(t_ind[j][k] - & yy[0], j, 1);

        return m;
      }

      //--------------------------------------------------------------------------------
      /**
       * Return a single row of the coincidence matrix, as a sparse vector.
       * The vector has unsorted indices.
       * First requested for inspectors.
       */
      template <typename It1, typename It2>
      inline void
      get_cm_row_sparse(size_type row, It1 begin_ind, It2 begin_nz, bool learnt =false) const
      {
        size_type j_start = (small ? cl_map[row] : row) * c_pool_size;
        size_type j_end = learnt ? j_start + c_nnz : j_start + c_pool_size;

        for (size_type j = j_start; j != j_end; ++j) {
          *begin_ind++ = small ? from_rf(row, ind_nz[j].first) : ind_nz[j].first;
          *begin_nz++ = *(ind_nz[j].second);
        }
      }

      //--------------------------------------------------------------------------------
      template <typename It1, typename It2>
      inline void getMasterLearnedCoincidence(size_type m, It1 rows, It2 cols)
      {
        NTA_ASSERT(m < n_masters);

        size_type c = (isCloned() && !small) ? inv_cl_map[m][0] : m;
        const IndNZ* p = row_begin(c);

        if (!small)
          for (size_type i = 0; i != c_nnz; ++i)
            to_rf(c, p[i].first, cols[i], rows[i]);
        else
          for (size_type i = 0; i != c_nnz; ++i) {
            cols[i] = p[i].first % c_rf_side;
            rows[i] = p[i].first / c_rf_side;
          }
      }

      //--------------------------------------------------------------------------------
      template <typename It1, typename It2>
      inline void getMasterHistogram(size_type m, It1 rows, It1 cols, It2 values)
      {
        NTA_ASSERT(m < n_masters);

        size_type c = (isCloned() && !small) ? inv_cl_map[m][0] : m;
        const IndNZ* p = row_begin(c);

        if (!small)
          for (size_type i = 0; i != c_pool_size; ++i) {
            to_rf(c, p[i].first, cols[i], rows[i]);
            values[i] = *p[i].second;
          }
        else
          for (size_type i = 0; i != c_pool_size; ++i) {
            cols[i] = p[i].first % c_rf_side;
            rows[i] = p[i].first / c_rf_side;
            values[i] = *p[i].second;
          }
      }

      //--------------------------------------------------------------------------------
    private:
      /**
       * Assumes active coincidences are listed in int_buffer. Doesn't modify int_buffer.
       */
      template <typename It>
      inline void learn(It x)
      {
        greater_2nd_p<size_type, value_type> order;

        // this changes the master histograms repeatedly
        if (small) {

          for (size_type i = 0; i != n_active; ++i) {

            size_type c = int_buffer[i];
            IndNZ *beg = row_begin(cl_map[c]);
            IndNZ *end = beg + c_pool_size;

            for (IndNZ* p = beg; p != end; ++p)
              *(p->second) += x[from_rf(c, p->first)];
          }

        } else { // not small

          for (size_type i = 0; i != n_active; ++i) {

            IndNZ *beg = row_begin(int_buffer[i]);
            IndNZ *end = beg + c_pool_size;

            for (IndNZ* p = beg; p != end; ++p)
              *(p->second) += x[p->first];
          }
        } // end not small case

        // now we can normlize the master histograms that were
        // touched, one by one, but each only once! (several
        // active coincidences might point to the same master
        // histogram)
        if (isCloned()) {

          std::set<size_type> touched_masters;

          if (small) {

            for (size_type i = 0; i != n_active; ++i) {

              // to make sure we don't normalize the same master
              // histogram twice
              size_type c = int_buffer[i];
              size_type master_index = cl_map[c];

              if (not_in(master_index, touched_masters)) {
                normalizeHistogram(master_index);
                touched_masters.insert(master_index);
              }
            }

            // and resort touched master
            set<size_type>::const_iterator it = touched_masters.begin();

            for (; it != touched_masters.end(); ++it) {
              IndNZ *beg = row_begin(*it);
              IndNZ *end = beg + c_pool_size;
              std::partial_sort(beg, beg + c_nnz, end, order);
            }

          } else { // not small

            for (size_type i = 0; i != n_active; ++i) {

              // to make sure we don't normalize the same master
              // histogram twice
              size_type master_index = cl_map[int_buffer[i]];

              if (not_in(master_index, touched_masters)) {
                normalizeHistogram(master_index);
                touched_masters.insert(master_index);
              }
            }

            // finally, resort all the touched coincidences
            // This step can re-order coincidences that were not touched, because
            // they share a master with a coincidence that was touched!
            std::vector<IndNZ> prev(c_pool_size);
            set<size_type>::const_iterator it = touched_masters.begin();

            for (; it != touched_masters.end(); ++it) {

              const std::vector<size_type>& clones = inv_cl_map[*it];
              IndNZ *beg = row_begin(clones[0]), *end = beg + c_pool_size;

              std::copy(beg, end, prev.begin());

              std::partial_sort(beg, beg + c_nnz, end, order);

              std::vector<size_type> a, b;

              for (size_type i = 0; i != c_nnz; ++i) {
                size_type idx = prev[i].first;
                bool changed_side = true;
                for (size_type j = 0; j != c_nnz; ++j)
                  if (beg[j].first == idx) {
                    changed_side = false;
                    break;
                  }
                if (changed_side) {
                  a.push_back(i);
                }
              }

              for (size_type i = c_nnz; i != c_pool_size; ++i) {
                size_type idx = prev[i].first;
                bool changed_side = false;
                for (size_type j = 0; j != c_nnz; ++j)
                  if (beg[j].first == idx) {
                    changed_side = true;
                    break;
                  }
                if (changed_side) {
                  b.push_back(i);
                }
              }

              std::copy(prev.begin(), prev.end(), beg);

              if (!a.empty()) {
                for (size_type j = 0; j != clones.size(); ++j) {
                  IndNZ *beg = row_begin(clones[j]);
                  for (size_type k = 0; k != a.size(); ++k)
                    std::swap(beg[a[k]], beg[b[k]]);
                }
              }
            }
          }

        } else {

          for (size_type i = 0; i != n_active; ++i) {

            size_type active = int_buffer[i];
            normalizeHistogram(active);

            IndNZ *beg = row_begin(active), *end = beg + c_pool_size;
            std::partial_sort(beg, beg + c_nnz, end, order);
          }
        }
      }

      //--------------------------------------------------------------------------------
      /**
       * The infer() method takes input vectors and produces output vectors that best
       * "represent" the input w.r.t. to the matrix of coincidences. The input, output
       * and coincidences are all sparse binary (0/1) vectors. The non-zeros of the output
       * correspond to the coincidences that best match the input vector. The output
       * always has constant sparsity (constant number of non-zeros = density),
       * according to FDR principles. The infer method has 2 parts, and optionally
       * calls update() to update the coincidences (if learning is on).
       *
       * This method takes in the input vector x and produces the result vector y which
       * the output of the SP itself. The input is a binary 0/1 vector of size input_width
       * (the size of the coincidences), and the output is another binary 0/1 vector,
       * of size input_height (the number of coincidences).
       *
       * 1. Compute matches:
       * ==================
       * This step computes the number of overlapping bits between the input and each
       * coincidence. This is achieved as follows:
       * Multiply current sparse matrix (in ind_nz) by x on the right, place result into
       * y. When doing that multiplication, for row i, we multiply up to ub[i] non-zeros
       * only: if we are not doing learning, ub[i] == c_nnz (set in constructor) ; if we are
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
       */
    public:
      template <typename It1, typename It2>
      inline void compute(It1 x, It1 x_end, It2 y, It2 y_end,
                          bool doLearn =false, bool doInfer =true)
      {
        { // Pre-conditions
          NTA_ASSERT((size_type)(x_end - x) == getInputSize());
          NTA_ASSERT((size_type)(y_end - y) == getNColumns());
        } // End pre-conditions

        size_type count = 0;

        size_type stimulus_threshold = doLearn ? stimulus_threshold_learning
          : stimulus_threshold_inference;

        for (It1 x_it = x; x_it != x_end && count <= stimulus_threshold; ++x_it)
          count += *x_it != 0;

        if (count <= stimulus_threshold) {
          std::fill(y, y_end, 0);
          return;
        }

        // use DirectAccess and multicolor board if this is slow,
        // to amortize the actual setting to 0
        set_to_zero(yy);

        if (t_ind.empty() && doInfer) {
          transpose();
          inhibition.setDesiredOutputDensity(desired_density_inference);
        } else if (!t_ind.empty() && doLearn) {
          t_ind.resize(0);
          inhibition.setDesiredOutputDensity(desired_density_learning);
        }

        // TODO: test that indices would be as fast as pointers
        // and replace pointers to avoid pointer size issues on 64-bits
        // platforms
        // TODO: combine transposition and inference, so
        // the transpose product works in learning too
        // TODO: can we compute on the transpose without computing
        // the transpose?
        // TODO: have the pointers in the transpose land on y directly
        // without indirection
        if (t_ind.empty()) {

          if (small) {

            for (size_type i = 0; i != c_field_size; ++i) {

              size_type m = cl_map[i];
              value_type s = 0.0f;
              size_type *p = &ind_nz[m * c_pool_size].first;
              size_type *p_end = p + P_INC * c_nnz;

              for (; p != p_end; p += P_INC)
                s += x[from_rf(i, *p)];

              yy[i] = s;
            }

          } else { // not small, faster

            for (size_type i = 0; i != c_field_size; ++i) {

              // *** HOTSPOT *** ??
              value_type s = 0.0f;
              size_type *p = &ind_nz[i * c_pool_size].first;
              size_type *p_end = p + P_INC * c_nnz;

              for (; p != p_end; p += P_INC)
                s += x[*p];

              yy[i] = s;
            }
          }

        } else {

          for (It1 it_x = x; it_x != x_end; ++it_x) {
            if (*it_x != 0) {
              size_type c = (size_type) (it_x - x);
              value_type **j = & t_ind[c][0];
              value_type **j_end = j + t_ind[c].size();
              for (; j != j_end; ++j)
                **j += *it_x;
            }
          }
        }

        if (!d_output.empty())
          std::copy(yy.begin(), yy.end(), d_output.begin());

        // 2. Impose constant output sparsity
        // puts results in int_buffer
        n_active = inhibition.compute(yy.begin(), &int_buffer[0],
                                      stimulus_threshold,
                                      doLearn ? convolution_k_learning
                                      : convolution_k_inference);

        if (doLearn && 0 < n_active)
          // looks at int_buffer, but doesn't modify it
          learn(x);

        to_dense_01(n_active, int_buffer, y, y_end);
      }

    public:
      //--------------------------------------------------------------------------------
      // PERSISTENCE
      //--------------------------------------------------------------------------------
      /**
       * This methods to pickle/unpickle a FDRCSpatial.
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
        }

        out_stream << version() << ' '
                   << (t_ind.empty() ? "0 " : "1 ")
                   << (int) small << ' '
                   << rng << ' '
                   << input_height << ' ' << input_width << ' '
                   << c_height << ' ' << c_width << ' '
                   << c_rf_radius << ' ' << c_pool_size << ' ' << c_nnz << ' '
                   << c_rf_side << ' ' << c_rf_size << ' '
                   << clone_height << ' ' << clone_width << ' '
                   << inhibition.getSmall() << ' '
                   << desired_density_learning << ' '
                   << desired_density_inference << ' '
                   << stimulus_threshold_learning << ' '
                   << stimulus_threshold_inference << ' '
                   << convolution_k_learning << ' '
                   << convolution_k_inference << ' '
                   << histogram_threshold << ' '
                   << normalization_sum << ' '
                   << hists << ' '
                   << n_active << ' '
                   << d_output.size() << ' ';

        size_type n = isCloned() ? n_masters : c_field_size;

        for (size_type i = 0; i != n; ++i) {

          size_type c = (isCloned() && !small) ? inv_cl_map[i][0] : i;
          const IndNZ* p = row_begin(c);

          for (size_type j = 0; j != c_pool_size; ++j) {

            size_type pos_in_input = p[j].first;
            size_type pos_in_rf = pos_in_input;

            if (isCloned() && !small)
              to_rf(c, pos_in_input, pos_in_rf);

            out_stream << pos_in_rf << " "
                       << (p[j].second - &hists[0])
                       << " ";
          }
        }
      }

      //--------------------------------------------------------------------------------
      inline void load(std::istream& in_stream)
      {
        {
          NTA_ASSERT(in_stream.good());
        }

        std::string ver;
        in_stream >> ver;

        if (ver != version()) {
          std::cout << "Incompatible version for fdr c sp: " << ver
                    << " - needs: " << version() << std::endl;
          exit(-1);
        }

        int dos = 0;
        int learn_infer_flag = 0;
        int is_small = 0;
        int small_inhibition = 0;

        in_stream >> learn_infer_flag >> is_small >> rng
                  >> input_height >> input_width
                  >> c_height >> c_width
                  >> c_rf_radius >> c_pool_size >> c_nnz
                  >> c_rf_side >> c_rf_size
                  >> clone_height >> clone_width
                  >> small_inhibition
                  >> desired_density_learning
                  >> desired_density_inference
                  >> stimulus_threshold_learning
                  >> stimulus_threshold_inference
                  >> convolution_k_learning
                  >> convolution_k_inference
                  >> histogram_threshold
                  >> normalization_sum
                  >> hists
                  >> n_active
                  >> dos;

        NTA_ASSERT(is_small == 0 || is_small == 1);
        small = (bool) is_small;
        input_size = input_height * input_width;
        c_field_size = c_height * c_width;
        n_masters = clone_height > 0 ? clone_height * clone_width : c_field_size;
        int_buffer.resize(std::max(c_field_size, c_rf_size), 0);

        std::vector<size_type> indnz;
        size_type n = isCloned() ? n_masters : c_field_size;
        indnz.resize(2 * n * c_pool_size);

        for (size_type i = 0; i != indnz.size(); ++i)
          in_stream >> indnz[i];

        initialize_cl_maps();
        initialize_rfs();
        initialize_ind_nz(&indnz[0]); // needs rfs and cl_maps
        inhibition.initialize(c_height, c_width,
                              learn_infer_flag == 0 ? desired_density_learning
                              : desired_density_inference, small_inhibition);

        d_output.resize(dos);

        yy.resize(getNColumns());
        if (learn_infer_flag == 1)
          transpose();

        { // Post-conditions
          NTA_ASSERT(!(isCloned() == false && small == true));
          NTA_ASSERT((clone_height == 0 && clone_width == 0)
                     || clone_height * clone_width != 0);
          NTA_ASSERT((small && ind_nz.size() == n_masters * c_pool_size)
                     || (!small && ind_nz.size() == c_field_size * c_pool_size));
          NTA_ASSERT(c_nnz <= c_pool_size);
          NTA_ASSERT(c_pool_size <= (2 * c_rf_radius + 1) * (2 * c_rf_radius + 1));
          NTA_ASSERT(0 < histogram_threshold);
          NTA_ASSERT(0 < normalization_sum);
        } // End post-conditions
      }

    private:
      //--------------------------------------------------------------------------------
      // If small, ind_nz stores only masters, otherwise it stores the full coincidences.
      inline size_type indNZNRows() const
      {
        return small ? n_masters : c_field_size;
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns a pointer to the first (index,value) pair of row i.
       */
      inline IndNZ* row_begin(size_type i)
      {
        return &ind_nz[0] + i * c_pool_size;
      }

      //--------------------------------------------------------------------------------
      /**
       * Returns a pointer to the first (index,value) pair of row i.
       */
      inline const IndNZ* row_begin(size_type i) const
      {
        return &ind_nz[0] + i * c_pool_size;
      }

      //--------------------------------------------------------------------------------
      /** KEEP: if not storing the clone map, this will give the master index for
          any coincidence index
      */
      inline size_type getMasterIndex(size_type row_index) const
      {
        return (row_begin(row_index)->second - &hists[0]) / c_pool_size;
      }

      //--------------------------------------------------------------------------------
      inline void
      to_rf(size_type c, size_type pos_in_input,
            size_type& x_in_rf, size_type& y_in_rf, size_type& pos_in_rf) const
      {
        NTA_ASSERT(c < c_field_size);
        NTA_ASSERT(pos_in_input < input_size);

        size_type lb_height = rfs[4*c];
        size_type lb_width = rfs[4*c+2];
        size_type x_in_input = pos_in_input % input_width;
        size_type y_in_input = pos_in_input / input_width;
        x_in_rf = x_in_input - lb_width;
        y_in_rf = y_in_input - lb_height;
        pos_in_rf = y_in_rf * c_rf_side + x_in_rf;

        NTA_ASSERT(x_in_rf < c_rf_side);
        NTA_ASSERT(y_in_rf < c_rf_side);
        NTA_ASSERT(pos_in_rf < c_rf_size);
      }

      //--------------------------------------------------------------------------------
      inline void
      to_rf(size_type c, size_type pos_in_input, size_type& pos_in_rf) const
      {
        size_type x_in_rf = 0, y_in_rf = 0;
        to_rf(c, pos_in_input, x_in_rf, y_in_rf, pos_in_rf);
      }

      //--------------------------------------------------------------------------------
      inline void
      to_rf(size_type c, size_type pos_in_input, size_type& x_in_rf, size_type& y_in_rf) const
      {
        size_type pos_in_rf = 0;
        to_rf(c, pos_in_input, x_in_rf, y_in_rf, pos_in_rf);
      }

      //--------------------------------------------------------------------------------
      inline void
      from_rf(size_type c, size_type pos_in_rf,
              size_type& x_in_input, size_type& y_in_input, size_type& pos_in_input) const
      {
        NTA_ASSERT(c < c_field_size);
        NTA_ASSERT(pos_in_rf < c_rf_size);

        size_type lb_height = rfs[4*c];
        size_type lb_width = rfs[4*c+2];
        size_type x_in_rf = pos_in_rf % c_rf_side;
        size_type y_in_rf = pos_in_rf / c_rf_side;
        x_in_input = x_in_rf + lb_width;
        y_in_input = y_in_rf + lb_height;
        pos_in_input = y_in_input * input_width + x_in_input;

        NTA_ASSERT(x_in_input < input_width);
        NTA_ASSERT(y_in_input < input_height);
        NTA_ASSERT(pos_in_input < input_size);
      }

      //--------------------------------------------------------------------------------
      inline size_type from_rf(size_type c, size_type pos_in_rf) const
      {
        size_type x, y, pos_in_input;
        from_rf(c, pos_in_rf, x, y, pos_in_input);
        return pos_in_input;
      }

      //--------------------------------------------------------------------------------
      /**
       * Normalize one histogram.
       */
      inline void normalizeHistogram(size_type i)
      {
        {
          NTA_ASSERT((isCloned() && i < getNMasters()) || i < getNColumns());
        }

        value_type* beg = &hists[0] + i * c_pool_size;
        value_type* end = beg + c_pool_size;
        value_type s = 1e-9f;

        for (value_type *p = beg; p != end; ++p)
          s += *p;

        value_type k = normalization_sum / s;

        for (value_type* p = beg; p != end; ++p)
          *p *= k;
      }

      //--------------------------------------------------------------------------------
      /**
       * Normalize all the histograms.
       */
      inline void normalize()
      {
        size_t n = isCloned() ? getNMasters() : getNColumns();

        for (size_type i = 0; i != n; ++i)
          normalizeHistogram(i);
      }

      //--------------------------------------------------------------------------------
      inline void transpose()
      {
        // TODO: maintain the transpose incrementally when doing the swaps
        // TODO: transpose only up to first c_nnz positions, or keep
        // whole transpose so we can use it in learning too??
        // TODO: interleave t_start and t_nnz for improved locality?
        // TODO: reduce type size to fit better in cache
        // TODO: speed-up by allocating columns in dense??
        // TODO: remove either t_start or t_nnzc, set up more pointers
        // for inference

        // if small, change sizes
        t_ind.resize(getInputSize());

        for (size_type i = 0; i != t_ind.size(); ++i)
          t_ind[i].clear();

        for (size_type i = 0; i != c_field_size; ++i) {
          size_type j = (small ? cl_map[i] : i) * c_pool_size;
          size_type j_end = j + c_nnz;
          for (; j != j_end; ++j) {
            size_type pos_in_input =
              small ? from_rf(i, ind_nz[j].first) : ind_nz[j].first;
            t_ind[pos_in_input].push_back(& yy[0] + i);
          }
        }
      }

      //--------------------------------------------------------------------------------
      nta::Random rng;

      size_type input_size, input_height, input_width;
      size_type c_height, c_width, c_field_size, c_rf_radius, c_pool_size, c_nnz;
      size_type c_rf_side, c_rf_size;
      size_type n_masters, clone_height, clone_width;
      value_type desired_density_learning;
      value_type desired_density_inference;
      size_type stimulus_threshold_learning;
      size_type stimulus_threshold_inference;
      value_type convolution_k_learning;
      value_type convolution_k_inference;
      value_type histogram_threshold;
      value_type normalization_sum;

      size_type n_active;
      bool small;
      std::vector<IndNZ> ind_nz;   // vectors of pairs <index,bit count *>
      std::vector<value_type> hists;
      std::vector<size_type> cl_map;
      std::vector<std::vector<size_type> > inv_cl_map;
      std::vector<size_type> int_buffer;
      std::vector<value_type> d_output;
      Inhibition inhibition;

      std::vector<value_type> yy;
      std::vector<std::vector<value_type*> > t_ind;

      std::vector<size_type> rfs;
    };

    //--------------------------------------------------------------------------------
  } // end namespace algorithms
} // end namespace nta

#endif // NTA_FDR_C_SPATIAL_HPP
