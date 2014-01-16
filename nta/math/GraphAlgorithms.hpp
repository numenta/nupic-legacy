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

/** @file 
 * Definition and implementation of graph algorithms
 */

#ifndef NTA_GRAPH_ALGORITHMS_HPP
#define NTA_GRAPH_ALGORITHMS_HPP

/**
 * Graph utilities. Not currently used in production code.
 */

#include <boost/unordered_set.hpp>
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/cuthill_mckee_ordering.hpp>
#include <boost/graph/properties.hpp>
#include <boost/graph/bandwidth.hpp>
#include <boost/graph/connected_components.hpp>

namespace nta {

  //--------------------------------------------------------------------------------
  // GRAPH ALGORITHMS
  //--------------------------------------------------------------------------------

  typedef std::vector<nta::UInt32> Sequence;
  typedef std::list<Sequence> Sequences;

  //--------------------------------------------------------------------------------
  /**
   * Enumerates all the sequences in this matrix by following edges that 
   * have a value greater than threshold th.
   *
   * row_sums = tam.rowSums(); col_sums = tam.colSums()
   * ratios = [c/r if r != 0 else 0 for r,c in zip(row_sums,col_sums)]
   * front = [[i] for i in range(tam.nRows()) if ratios[i] >= threshold]
   * seqs = []
   * 
   * while front:
   *  subseq = front[0]; l = len(subseq); p = subseq[-1]
   *  cands = tam.colNonZeros(p)[0]
   *  next = [n for n in cands if tam[n,p] > min_count and n not in subseq]
   *  if next:
   *   for n in next:
   *    front.insert(1, subseq+[n])
   *  elif l > 1 and is_sublist_of(subseq, seqs) == -1:
   *   seqs.append(subseq)
   * front.pop(0)
   */
  template <typename SM>
  inline void 
  EnumerateSequences(typename SM::value_type th, const SM& g, Sequences& sequences,
		     int rowsOrCols=0, int noSubsequences=0)
  {
    using namespace std;

    typedef typename SM::size_type size_type;
    typedef typename SM::value_type value_type;

    const size_type N = rowsOrCols == 0 ? g.nCols() : g.nRows();
    Sequences front;
    vector<size_type> ind(N);
    vector<value_type> nz(N);

    for (size_type i = 0; i != N; ++i) {
      Sequence s; s.push_back(i); front.push_back(s);
    }

    while (!front.empty()) {
      Sequence ss = front.front();
      bool more = false;
      size_type l = ss.size(), p = ss[l-1];
      size_type n = 0;
      if (rowsOrCols == 1)
        n = g.getColToSparse(p, ind.begin(), nz.begin());
      else
        n = g.getRowToSparse(p, ind.begin(), nz.begin());
      for (size_type i = 0; i != n; ++i) {
        if (nz[i] > th && !contains(ss, ind[i])) {
          more = true;
          Sequence new_seq(ss);
          new_seq.push_back(ind[i]);
          front.insert(++front.begin(), new_seq);
        }
      }
      if (!more && l > 1) {
        if (noSubsequences && !is_subsequence_of(sequences, ss))
          sequences.push_back(ss);
        else
          sequences.push_back(ss);
      }
      front.pop_front();
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Finds connected components using a threshold.
   * The returned components are not sorted.
   *
   * groups = []
   * cands = set(range(tam.nRows()))
   * 
   * while cands:
   *  front = [cands.pop()]
   *  more = True
   *  while more:
   *   new_front = [] 
   *   for x in front:
   *    cnz = tam.colNonZeros(x); rnz = tam.rowNonZeros(x)
   *    for n in [i for i,v in zip(cnz[0],cnz[1]) if v > th and i in cands]:
   *     new_front += [n]; cands.remove(n)
   *    for n in [i for i,v in zip(rnz[0],rnz[1]) if v > th and i in cands]:
   *     new_front += [n]; cands.remove(n)
   *   if len(new_front) > 0:
   *    front += new_front
   *   else: 
   *    groups.append(front)
   *    more = False
   *
   */
  /*
    groups = []
    cands = set(range(tam.nRows()))
    ttam = copy.deepcopy(tam)
    ttam.transpose()

    while cands:

    front = set([cands.pop()])
    groups.append(list(front))
    g = groups[-1]

    while front:
    new_front = set([])
    for x in front:
    rnz = tam.rowNonZeros(x); cnz = ttam.rowNonZeros(x)
    l = zip(rnz[0],rnz[1]) + zip(cnz[0],cnz[1])
    for n,v in l:
    if v > th and n in cands:
    new_front.add(n); g += [n]; cands.remove(n)
    front = new_front
  */
  template <typename SM>
  inline void 
  FindConnectedComponents(typename SM::value_type th, const SM& g, Sequences& components) 
  {
    using namespace std;
    using namespace boost;

    typedef typename SM::size_type size_type;
    typedef typename SM::value_type value_type;
    typedef unordered_set<size_type> Set;

    const size_type N = g.nRows();
    
    vector<size_type> ind(2*N);
    vector<value_type> nz(2*N); 
    
    Set cands;
    typename Set::iterator x, w;
    
    for (size_type i = 0; i != N; ++i)
      cands.insert(i);
      
    SM tg;
    g.transpose(tg);

    while (!cands.empty()) {

      size_type seed = *cands.begin();
      cands.erase(seed);
      
      Sequence group;   
      group.push_back(seed);
      
      Set front;
      front.insert(seed);
      
      while (!front.empty()) {
        
        Set new_front;

        for (x = front.begin(); x != front.end(); ++x) {

          size_type n = g.getRowToSparse(*x, ind.begin(), nz.begin());
          n += tg.getRowToSparse(*x, ind.begin()+n, nz.begin()+n);

          for (size_type j = 0; j != n; ++j) {
            size_type y = ind[j];
            if (nz[j] > th && (w = cands.find(y)) != cands.end()) {
              new_front.insert(y); group.push_back(y);
              cands.erase(w);
            }
          }
        }
        front.swap(new_front);
      }
      components.push_back(group);
    }
  }
  
  //--------------------------------------------------------------------------------
  /**
   * This for unit testing. 
   * The returned components are sorted.
   */
  template <typename SM>
  inline void FindConnectedComponents_boost(const SM& sm, Sequences& components)
  {
    using namespace std;
    using namespace boost;

    typedef typename SM::size_type size_type;
    typedef typename SM::value_type value_type;
    typedef adjacency_list <vecS, vecS, undirectedS> Graph;
    
    Graph G(sm.nCols());
    size_type n = sm.nNonZeros();
    vector<size_type> nz_i(n), nz_j(n);
    vector<value_type> nz_v(n);

    sm.getAllNonZeros(nz_i.begin(),nz_j.begin(),nz_v.begin());

    for (size_type i = 0; i != n; ++i) 
      add_edge(nz_i[i],nz_j[i], G);

    std::vector<int> component(num_vertices(G));
    int num = connected_components(G, &component[0]);

    vector<Sequence> c(num);
    
    for (size_type i = 0; i != component.size(); ++i) 
      c[component[i]].push_back(i);
    
    for (int i = 0; i != num; ++i)
      components.push_back(c[i]);
  }
 
  //--------------------------------------------------------------------------------
  //--------------------------------------------------------------------------------
  template <typename SM, typename OutputIterator>
  inline void CuthillMcKeeOrdering(const SM& sm, OutputIterator p, OutputIterator rp)
  {
    using namespace std;
    using namespace boost;

    typedef typename SM::size_type size_type;
    typedef typename SM::value_type value_type;
    
    typedef adjacency_list<vecS,vecS, undirectedS, 
      property<vertex_color_t, default_color_type,
      property<vertex_degree_t,int> > > Graph;
    typedef graph_traits<Graph>::vertex_descriptor Vertex;
    
    const size_type nrows = sm.nRows();

    Graph G(nrows);

    for (size_type i = 0; i != nrows; ++i) {
      const size_type* ind = sm.row_nz_index_begin(i);
      const size_type* ind_end = sm.row_nz_index_end(i);
      for (; ind != ind_end; ++ind)
	add_edge(i, *ind, G);
    }

    graph_traits<Graph>::vertex_iterator ui, ui_end;

    property_map<Graph,vertex_degree_t>::type deg = get(vertex_degree, G);
    for (boost::tie(ui, ui_end) = vertices(G); ui != ui_end; ++ui)
      deg[*ui] = degree(*ui, G);

    property_map<Graph, vertex_index_t>::type
      index_map = get(vertex_index, G);

    std::cout << "original bandwidth: " << bandwidth(G) << std::endl;

    std::vector<Vertex> inv_perm(num_vertices(G));
    std::vector<size_type> perm(num_vertices(G));

    size_type best = nrows;

    for (size_type i = 1; i != nrows; ++i) {

      Vertex s = vertex(i, G);

      //reverse cuthill_mckee_ordering
      cuthill_mckee_ordering(G, s, inv_perm.rbegin(), get(vertex_color, G), 
			     get(vertex_degree, G));
      /*
      cout << "  ";    
      for (std::vector<Vertex>::const_iterator i = inv_perm.begin();
	   i != inv_perm.end(); ++i)
	cout << index_map[*i] << " ";
      */

      for (size_type c = 0; c != inv_perm.size(); ++c)
	perm[index_map[inv_perm[c]]] = c;

      size_type bw = 
	bandwidth(G, make_iterator_property_map(&perm[0], index_map, perm[0]));

      if (bw < best) {
	best = bw;
	std::cout << "bandwidth: " 
		  << bw
		  << std::endl;
	std::copy(perm.begin(), perm.end(), p);
	std::copy(inv_perm.begin(), inv_perm.end(), rp);
      }
    }
  }

  //--------------------------------------------------------------------------------
} // end namespace nta
#endif //GRAPH_ALGORITHMS
