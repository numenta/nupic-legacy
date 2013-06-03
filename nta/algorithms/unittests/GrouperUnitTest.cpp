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

/** @file
 * Implementation for Grouper unit tests
 */

#include <nta/algorithms/Grouper.hpp>
#include <nta/os/FStream.hpp>
#include "GrouperUnitTest.hpp"

using namespace std;

namespace nta {
//
//  //--------------------------------------------------------------------------------
//  struct GrouperUnitTestReader
//  {
//    typedef vector<pair<int, vector<Grouper::IdxVal> > > Winners;
//    typedef Grouper::IntegerTAM IntegerTAM;
//    typedef map<Size, IntegerTAM*> TAMS;
//    typedef map<Size, Grouper::Groups> Groups;
//
//    Size transitionMemory;   
//    Size topNeighbors;
//    Size maxGroupSize;
//    string flag;
//    Winners winners;  // vector of winningCoincIdx, [<coincIdx, count>, coincIdx,count>...]
//    TAMS tams;        // key is the index from the tam file, value is the tam 
//    Groups groups;    // key is the index from the groups file, value is a vector of sets 
//
//    GrouperUnitTestReader(const std::string& tc)
//      : transitionMemory(0),
//        topNeighbors(0),
//        maxGroupSize(0),
//        flag(""),
//        winners(),
//        tams(),
//        groups()
//    {
//      string ss;
//      const string s = Tester::fromTestInputDir(ss);
//      readParamsFile(s + "/grouping/params-" + tc + ".txt");
//      readWinnersFile(s + "/grouping/winner-" + tc + ".txt", false);
//      readTAMFile(s + "/grouping/tam-" + tc + ".txt", false);
//      readGroupsFile(s + "/grouping/groups-" + tc + ".txt");
//    }
//
//    /*
//     * Read in the params file.
//     * Format is:
//     *   transitionMemory topNeighbors maxGroupSize tamKind
//     *
//     * Where tamKind is either 'symmetric' or 'assymmetric'
//     */
//    void readParamsFile(const std::string& paramFileName)
//    {
//      IFStream paramFile(paramFileName.c_str());
//      paramFile >> transitionMemory >> topNeighbors >> maxGroupSize
//                >> flag;
//      paramFile.close();
//    }
//
//    /*
//     * Read in the winner file.
//     * Format is:
//     *    numSamples
//     *    sampleIdx winnerCoinc coincCounts count[0] count[1] ...
//     *    ...
//     */
//    void readWinnersFile(const std::string& winnerFileName, bool playback =false)
//    {
//      int winner;
//      Size n1, n2, idx;
//      IFStream winnerFile(winnerFileName.c_str());
//      NTA_CHECK(winnerFile) << "Unable to open file " << winnerFileName;
//      winnerFile >> n1;
//      for (Size i = 0; i < n1; ++i) {
//        winnerFile >> idx >> winner >> n2;
//        if (playback)
//          NTA_INFO << "Idx = " << idx << " winner = " << winner;
//        vector<Grouper::IdxVal> counts;
//        Real count;
//        for (UInt j = 0; j < n2; ++j) {
//          winnerFile >> count;
//          counts.push_back(make_pair(j, (UInt)count));
//          if (playback)       
//            NTA_INFO << " " << count;
//        }
//        if (playback)
//          NTA_INFO << endl;
//        winners.push_back(make_pair(winner, counts));
//      }
//      winnerFile.close();
//    }
//
//    /* Read in the TAM file.
//     * Format is:
//     *   numSamples
//     *   sampleIdx dimension numElements element0 element1 ....
//     *   ...
//     */
//    void readTAMFile(const std::string& tamFileName, bool playback =false)
//    {
//      if (playback)
//        NTA_INFO << "TAM file: " << tamFileName << endl;
//
//      Size n1, idx, nelts;
//      UInt dim;
//      IFStream tamFile(tamFileName.c_str());
//      tamFile >> n1;
//      for (Size i = 0; i < n1; ++i) {
//        tamFile >> idx >> dim >> nelts;
//        if (playback) {
//          NTA_INFO << "Idx = " << idx << " ";
//        }
//        vector<UInt> mat;
//        mat.resize(nelts);
//        Real val;
//        for (UInt j = 0; j < nelts; ++j) {
//          tamFile >> val; 
//          mat[j] = UInt(val);
//          if (playback) {
//            NTA_INFO << mat[j] << " ";
//          }
//        }
//        if (playback)
//          NTA_INFO << endl;
//        IntegerTAM* tam = new IntegerTAM(dim, dim);
//        tam->fromDense(dim, dim, &mat[0]);
//        tams[idx] = tam;
//      }
//
//      tamFile.close();
//    }
//  
//    /* Read in the groups file
//     * Format is:
//     *    numSamples
//     *    sampleIdx numGroups grp0Len grp0Member0 ... grp1Len grp1Member0 ...
//     *    ...
//     */
//    void readGroupsFile(const std::string& groupFileName)
//    {
//      Size n1, idx, n2, len, id;
//      IFStream groupsFile(groupFileName.c_str());
//      groupsFile >> n1;
//      for (Size i = 0; i < n1; ++i) {
//        groupsFile >> idx >> n2;
//        Grouper::Groups aGroupOfSets;       // A vector of sets
//        for (Size j = 0; j < n2; ++j) {
//          groupsFile >> len;
//          Grouper::AGroup grp;              // A set
//          for (Size k = 0; k < len; ++k) {
//            groupsFile >> id;
//            grp.insert((UInt)id);
//          }
//          aGroupOfSets.push_back(grp);
//        }
//        groups[idx] = aGroupOfSets;
//      }
//      groupsFile.close();
//    }
//
//    ~GrouperUnitTestReader() 
//    {
//      map<Size, IntegerTAM*>::const_iterator it;
//      for (it = tams.begin(); it != tams.end(); ++it)
//        delete it->second;
//    }
//
//    static void printGroups(const Grouper::Groups& groups) 
//    {
//      Grouper::Groups::const_iterator it;
//      UInt grpIdx = 0;
//      for (it = groups.begin(); it != groups.end(); ++it, ++grpIdx) {
//        Grouper::AGroup::const_iterator eit;
//        stringstream ss;
//        ss << "  Group " << grpIdx << ": ";
//        for (eit = it->begin(); eit != it->end(); ++eit)
//          ss << *eit << " ";
//        NTA_INFO << ss.str();
//      }
//    }
//
//    bool compareTams(const IntegerTAM& tam1, const IntegerTAM& tam2) const
//    {
//      const Size N = tam1.nRows();
//      if (flag == "symmetric") {
//        for (UInt i = 0; i < N; ++i) 
//          for (UInt j = 0; j <= i; ++j) 
//            if (tam1.get(i, j) != tam2.get(i, j))
//              return false;
//      } else {
//        for (UInt i = 0; i < N; ++i) 
//          for (UInt j = 0; j < N; ++j) 
//            if (tam1.get(i, j) != tam2.get(i, j))
//              return false;
//      }
//      
//      return true;
//    }
//
//
//    bool compareOutputs(const vector<Real>& vec1, const vector<Real>& vec2) const
//    {
//      if (vec1.size() != vec2.size()) return false;
//      for (UInt i=0; i<vec1.size(); i++) 
//      {
//        if (!nearlyEqual(vec1[i], vec2[i]))
//          return false;
//      }
//      return true;
//    }
//
//
//    bool compareGroups(const Grouper::Groups& g1, const Grouper::Groups& g2) const
//    {
//      if (g1.size() != g2.size()) {
//        NTA_INFO << "Groups sizes are different";
//        return false;
//      }
//      
//      Grouper::Groups::const_iterator it1, it2;
//      for (it1 = g1.begin(), it2 = g2.begin(); it1 != g1.end(); ++it1, ++it2) {
//        vector<Size> diff;
//        set_symmetric_difference(it1->begin(), it1->end(),
//                                 it2->begin(), it2->end(),
//                                 back_inserter(diff));
//        if (!diff.empty()) {
//          NTA_INFO << "Groups are not identical as sets";
//          return false;  
//        }
//      }  
//      
//      return true;
//    }
//  };
//
//
//  //--------------------------------------------------------------------------------
//  /*
//    This works by feeding a bunch of coincidences into the grouper to have it learn specific
//    groups. We then test the inference output by feeding in specific coincidences and
//    checking the output.
//   */
//  void GrouperUnitTest::testTBI(bool diagnose)
//  {
//    const char* prefix = "GrouperUnitTest::testTBI() - ";
//    
//    // -------------------------------------------------------------------------------
//    // Instantiate the grouper
//    // Notice that we set the transition history memory (mem) to 1. This makes our
//    // TAM "cleaner" such that we only have entries on the coincidence immediately
//    // preceding each other coincidence. The TBI will work with any value of mem,
//    // but the increase in output going forward in the group vs going backward in the
//    // group is more dramatic when mem is 1.
//    Grouper g(1 /*transitionMem*/, 2 /*topNeighbors*/, 9999 /*maxGroups*/, 
//              4 /*maxGroupSize*/, false /*symmetric*/, false /*overlappingGroups*/,
//              1 /*ahc large group penalty*/, Grouper::tbi);
//    
//    // -----------------------------------------------------------------------------
//    // Feed in the data to train the grouper. We are trying to train it to learn 2 
//    //  groups 0,1,2,3 and 4,5,6,7. 
//    const UInt numCoinc = 8;
//    vector<Grouper::IdxVal> counts(numCoinc);
//    for (UInt i=0; i<numCoinc; i++)
//      counts[i] = make_pair(i, 0);
//      
//    std::vector<Size> empty;
//    const UInt iterations = 100;
//    for (UInt i=0; i<iterations; i++) {
//      for (UInt winner = 0; winner < 4; winner++) {
//        counts[winner].second++;
//        g.learn(&winner, empty.begin());
//      }
//    }
//    for (UInt i=0; i<iterations; i++) {
//      for (UInt winner = 4; winner < numCoinc; winner++) {
//        counts[winner].second++;
//        g.learn(&winner, empty.begin());
//      }
//    }
//    
//    // --------------------------------------------------------------------------------
//    // Do the grouping
//    g.group(counts);
//    
//    // Print diagnostics
//    if (diagnose) {
//      // Print the groups
//      NTA_INFO << prefix << "Groups:";
//      GrouperUnitTestReader::printGroups(g.getGroups());
//      
//      // Print the cell weights and cell outputs for each group
//      for (UInt grpIdx = 0; grpIdx < g.getNGroups(); grpIdx++)
//      {
//        NTA_INFO << prefix << "TBI Cell Weights[" << grpIdx << "]" << "\n" 
//                 << g.getTBIWeights(grpIdx);
//        NTA_INFO << prefix << "TBI Cell Outputs[" << grpIdx << "]" << "\n" 
//                 << g.getTBICellOutputs(grpIdx);
//      }
//    }
//
//    // --------------------------------------------------------------------------------
//    // Test inference going forward in group 0. This is the group with coincidences
//    //  0,1,2,3
//    Grouper::Groups groups = g.getGroups();
//    UInt  inputSize = g.tam_.nCols();
//    UInt  outputSize = (UInt) groups.size();
//    vector<Real> input(inputSize, 0);
//    vector<Real> output(outputSize, 0);
//    
//    Real prevCertainty = 0.0;
//    for (UInt idx=0; idx < 4; idx++)
//    {
//      fill(input.begin(), input.end(), (Real)0);
//      input[5] = 0.5;      // some amount in group 1
//      input[idx] = 1.0;   
//      g.infer(input.begin(), input.end(), output.begin());
//      
//      if (diagnose) {
//        NTA_INFO << prefix << "Group 0 Infer input: " << input << " output:" <<  output;
//        NTA_INFO << prefix << "Group 0 TBI Cell Outputs[0]" << "\n" 
//                 << g.getTBICellOutputs(0);
//      }
//      
//      // Make sure the output we expected is the winner
//      TEST(output[0] > output[1]);
//      
//      // Make sure we get more confident after each time step
//      Real certainty = output[0] / output[1];
//      if (idx > 0)
//        TEST(certainty > prevCertainty * 1.1);
//      prevCertainty = certainty;     
//    }
//
//    // --------------------------------------------------------------------------------
//    // Test inference going forward in group 1. This is the group with coincidences
//    //  4,5,6,7
//    g.resetTBIHistory();
//    for (UInt idx=4; idx < numCoinc; idx++)
//    {
//      fill(input.begin(), input.end(), (Real)0);
//      input[0] = 0.5;      // some amount in group 0
//      input[idx] = 1.0;   
//      g.infer(input.begin(), input.end(), output.begin());
//      
//      if (diagnose) {
//        NTA_INFO << prefix << "Group 1 Infer input: " << input << " output:" <<  output;
//        NTA_INFO << prefix << "Group 1 TBI Cell Outputs[0]" << "\n" 
//                 << g.getTBICellOutputs(1);
//      }
//      
//      // Make sure the output we expected is the winner
//      TEST(output[1] > output[0]);
//      
//      // Make sure we get more confident after each time step
//      Real certainty = output[1] / output[0];
//      if (idx > 4)
//        TEST(certainty > prevCertainty * 1.1);
//      prevCertainty = certainty;     
//    }
//
//    // --------------------------------------------------------------------------------
//    // Test inference going backward in group 0. Here, the output should stay constant     
//    g.resetTBIHistory();
//    for (Int idx=3; idx >= 0; idx--)
//    {
//      fill(input.begin(), input.end(), (Real)0);
//      input[5] = 0.5;      // some amount in group 1
//      input[idx] = 1.0;   
//      g.infer(input.begin(), input.end(), output.begin());
//      
//      if (diagnose) {
//        NTA_INFO << prefix << "Group 0 Bwd Infer input: " << input << " output:" <<  output;
//        NTA_INFO << prefix << "Group 0 Bwd TBI Cell Outputs[0]" << "\n" 
//                 << g.getTBICellOutputs(0);
//      }
//      
//      // Make sure the output we expected is the winner
//      TEST(output[0] > output[1]);
//      
//      // Make sure the certainty is roughly the same each time
//      Real certainty = output[0] / output[1];
//      if (idx < 3)
//        TEST(nearlyEqual(certainty,prevCertainty));
//      prevCertainty = certainty;     
//    }
//  }
//  
//  //--------------------------------------------------------------------------------
//  void GrouperUnitTest::testInference(Grouper& g, bool diagnose)
//  {
//    //diagnose = true;
//    
//    // Get the groups out, this is a vector of sets
//    Grouper::Groups groups = g.getGroups();
//    
//    // Get the size of the input and output. 
//    UInt  inputSize = g.tam_.nCols();
//    UInt  outputSize = (UInt) groups.size();
//  
//    // Allocate space for the input and output
//    vector<Real> input(inputSize, 0);
//    vector<Real> output(outputSize, 0);
//    
//    // Test each mode
//    const UInt numModes = 3;
//    Grouper::Mode modes[numModes] = {Grouper::maxProp, Grouper::sumProp, Grouper::tbi};
//    string        modeNames[numModes] = {"maxProp", "sumProp", "tbi"};
//
//    for (UInt modeIdx = 0; modeIdx < numModes; modeIdx++) 
//    {
//      // Set the inference mode
//      g.setMode(modes[modeIdx]);
//      std::string inferMode = modeNames[modeIdx];
//      
//      // -----------------------------------------------------------------------
//      // Iterate over each of the groups
//      Grouper::Groups::const_iterator groupsIt, groupsItEnd = groups.end();
//      UInt groupIdx = 0;
//      for (groupsIt = groups.begin(); groupsIt != groupsItEnd; ++groupsIt, ++groupIdx) 
//      {
//        vector<Real> outputSum(outputSize, 0);
//        
//        
//        // ---------------------------------------------------------------------
//        // First drive one element of the group at a time
//        Grouper::AGroup group = *groupsIt;
//        Grouper::AGroup::const_iterator it, end = group.end();
//        for (it = group.begin(); it != group.end(); ++it) {
//          fill(input.begin(), input.end(), (Real)0);
//          input[*it] = 1.0;
//          
//          g.infer(input.begin(), input.end(), output.begin());
//    
//          if (diagnose) {
//            NTA_INFO << inferMode << " inference, Group: " << groupIdx 
//		     << " input:" << input
//                     << "\noutput:" << output;
//          }
//          
//          // Sum the group output for each coincidence in the current group
//          for (UInt i=0; i<outputSize; ++i)
//            outputSum[i] += output[i];
//            
//        }
//        
//        // If we are running maxProp or tbi, the tested group's output should have been 
//        // 1 each time
//        if (inferMode == "maxProp" || inferMode == "tbi") {
//          for (UInt i=0; i<outputSize; ++i) {
//            TEST(i == groupIdx ? nearlyEqual(outputSum[i], (Real)group.size()) 
//                            : nearlyEqual(outputSum[i], (Real)0));
//          }
//
//        // If we are running sumProp, the tested group's output should sum to 1
//        } else if (inferMode == "sumProp") {
//           for (UInt i=0; i<outputSize; ++i) {
//            TEST(i == groupIdx ? nearlyEqual(outputSum[i], (Real)1) 
//                            : nearlyEqual(outputSum[i], (Real)0));
//           }
//        }
//
//
//        // --------------------------------------------------------------------------
//        // Now, drive all elements of the group
//        fill(input.begin(), input.end(), (Real)0);
//        for (it = group.begin(); it != group.end(); ++it) 
//          input[*it] = 1.0;
//          
//        g.infer(input.begin(), input.end(), output.begin());
//        if (diagnose) {
//          NTA_INFO << inferMode << " inference, Group: " << groupIdx << " input:" << input
//                     << "\noutput:" << output;
//        }
//
//        // In both all modes, the tested group's output should be 1
//        for (UInt i=0; i<outputSize; ++i) {
//          TEST(
//            i == groupIdx ? nearlyEqual(output[i], (Real)1) 
//                          : nearlyEqual(output[i], (Real)0));
//        }
//
//      } // for (groupsIt = ...)
//      
//    } // for (UInt modeIdx = 0; modeIdx < numModes; modeIdx++) 
//  }
//  
//
//  //--------------------------------------------------------------------------------
//  void GrouperUnitTest::doOneTestCase(const std::string& tcName, bool diagnose)
//  {
//    GrouperUnitTestReader data(tcName);
//    GrouperUnitTestReader::TAMS::const_iterator tam_it;   
//    GrouperUnitTestReader::Groups::const_iterator grp_it;
//    
//    // Note: The specific grouper mode passed in here is irrelevant for learning mode,
//    // when we do the inference test, we test inference on each of the modes. 
//    Grouper g((UInt)data.transitionMemory, (UInt)data.topNeighbors, 9999 /*maxGroups*/, 
//              (UInt)data.maxGroupSize, 
//              data.flag == "symmetric", false /*overlappingGroups*/, 
//	      1 /*ahc large group penalty*/, Grouper::maxProp);
//
//    // Feed in the learning samples one by one, and compare the groups formed after
//    // each sample
//    for (Size i = 0; i < data.winners.size(); ++i) 
//    {
//      int winner = data.winners[i].first;  // winning coincidence index
//      vector<Grouper::IdxVal> counts = data.winners[i].second; // vector of <coincIdx,count>
//            
//      if (diagnose) {
//        NTA_INFO << "Winner: " << winner << " - counts = ";
//        for (Size j = 0; j < counts.size(); ++j)
//          NTA_INFO << counts[j].first << ":" << counts[j].second << " ";
//        NTA_INFO << endl;
//      }
//    
//      if (winner < 0) {
//        g.resetHistory();
//      } else {      
//        std::vector<Size> empty;
//        g.learn(&winner, empty.begin());
//      }   
//
//      tam_it = data.tams.find(i);
//      if (tam_it != data.tams.end()) {
//
//        Grouper::IntegerTAM sym_tam(g.tam_);
//        
//        if (data.flag == "symmetric") {
//          Grouper::IntegerTAM tam2(1,1);
//          tam2.resize(sym_tam.nCols(), sym_tam.nCols());
//          sym_tam.transpose(tam2);
//          sym_tam.lerp(1, 1, tam2); 
//        }  
//
//        if (diagnose) {      
//          NTA_INFO << "Grouper TAM: "    
//                   << sym_tam.nRows() << " "
//                   << sym_tam.nCols() << endl 
//                   << sym_tam << endl;
//          NTA_INFO << "Ref TAM: " 
//                   << tam_it->second->nRows() << " "
//                   << tam_it->second->nCols() << endl
//                   << *(tam_it->second) << endl;
//        }
//
//        TEST(data.compareTams(sym_tam, *(tam_it->second)));
//	if (!data.compareTams(sym_tam, *(tam_it->second)))
//	  exit(-1);
//      }
//
//      grp_it = data.groups.find(i);
//      if (grp_it != data.groups.end()) 
//      {
//        g.group(counts);
//
//        if (diagnose) {
//          NTA_INFO << "Ref groups: " << endl; 
//          data.printGroups(grp_it->second);
//          NTA_INFO << "Grouper groups: " << endl;
//          data.printGroups(g.groups_);
//        }
//
//        Grouper::Groups groups = g.getGroups();
//
//        Grouper::Groups::const_iterator it;
//        for (it = groups.begin(); it != groups.end(); ++it) 
//          TEST(it->size() <= data.maxGroupSize);
//      
//        TEST(data.compareGroups(groups, grp_it->second));
//      } // if (grp_it != data.groups.end())
//      
//    } // for (Size i = 0; i < data.winners.size(); ++i)
//  
//  // Test inference after we've fed in the last learning sample for this test. This 
//  // will test all inference modes
//  testInference(g, diagnose);
//  
//  } // GrouperUnitTest::doOneTestCase
//
//
//  //--------------------------------------------------------------------------------
//  void GrouperUnitTest::testSaveReadState()
//  {
//    vector<string> tcs;
//    tcs.push_back(string("0"));
//    tcs.push_back(string("1"));
//    tcs.push_back(string("2"));
//    tcs.push_back(string("3"));
//    tcs.push_back(string("4"));
//    tcs.push_back(string("5"));
//    tcs.push_back(string("6"));
//    tcs.push_back(string("7"));
//    tcs.push_back(string("8"));
//
//    std::vector<Size> empty;
//
//    for (Size n = 0; n < tcs.size(); ++n) {
//
//      GrouperUnitTestReader data(tcs[n]);
//      GrouperUnitTestReader::TAMS::const_iterator tam_it;
//      GrouperUnitTestReader::Groups::const_iterator grp_it;
//
//      // Test each mode
//      const UInt numModes = 2;
//      Grouper::Mode modes[numModes] = {Grouper::maxProp, Grouper::sumProp};
//      //string        modeNames[numModes] = {"maxProp", "sumProp"};
//
//      for (UInt modeIdx = 0; modeIdx < numModes; modeIdx++) {
//
//	{ // Simulate saving and reading back  
//	  Grouper g((UInt)data.transitionMemory, (UInt)data.topNeighbors, 
//		    (UInt)data.maxGroupSize, 9999, 
//		    data.flag == "symmetric", false, 
//		    1 /*ahc large group penalty*/, modes[modeIdx]);
//
//	  for (Size i = 0; i < data.winners.size(); ++i) {
//
//	    int winner = data.winners[i].first;
//	    vector<Grouper::IdxVal> counts = data.winners[i].second;
//                 
//	    if (winner < 0) {
//	      g.resetHistory();  
//	    } else {
//	      g.learn(&winner, empty.begin());
//	    }
//     
//	    grp_it = data.groups.find(i);
//	    if (grp_it != data.groups.end()) 
//	      g.group(counts);
//              
//	    // Perform an inference. Only TBI mode will typically be affected by inference
//	    Grouper::Groups groups = g.getGroups();
//	    UInt  inputSize = g.tam_.nCols();
//	    UInt  outputSize = (UInt) groups.size();
//	    vector<Real> input(inputSize, 0);
//	    input[0] = 1.0;
//	    vector<Real> output(outputSize, 0);
//	    g.infer(input.begin(), input.end(), output.begin());
//           
//	    // Save the state
//	    stringstream ref, buf, buf2;
//	    g.saveState(ref);    
//	    g.saveState(buf);
//            
//	    // Instantiate a new grouper from the saved state, and then save it's state
//	    Grouper g2(buf);
//	    g2.saveState(buf2);
//            
//	    // Make sure the saved state agrees between the 2 instantiated groupers
//	    TEST(ref.str() == buf2.str());
//
//	    if (ref.str() != buf2.str())
//	      return;
//                                                                
//	    // To verify that TBI mode saved the correct state, compare the inference
//	    //  output of the 2 groupers after saving and restoring state
//	    g.infer(input.begin(), input.end(), output.begin());
//	    vector<Real> output2(outputSize, 0);
//	    g2.infer(input.begin(), input.end(), output2.begin());
//	    TEST(data.compareOutputs(output, output2));
//
//	    if (!data.compareOutputs(output, output2))
//	      return;
//            
//	  } // for (Size i = 0; i < data.winners.size(); ++i)
//	} // // Simulate saving and reading back 
//
//	{ // simulates checkpointing and resuming
//	  Grouper g((UInt)data.transitionMemory, (UInt)data.topNeighbors, 
//		    (UInt)data.maxGroupSize, 9999, 
//		    data.flag == "symmetric", false, 
//		    1 /*ahc large group penalty*/, modes[modeIdx]);
//          
//	  for (Size i = 0; i < data.winners.size(); ++i) {
//            
//	    int winner = data.winners[i].first;
//	    vector<Grouper::IdxVal> counts = data.winners[i].second;
//            
//	    stringstream buf, buf1, buf2;
//	    g.saveState(buf);
//          
//	    Grouper g2(buf);
//
//	    if (winner < 0) {
//	      g.resetHistory();  
//	      g2.resetHistory();
//	    } else {
//	      g.learn(&winner, empty.begin());
//	      g2.learn(&winner, empty.begin());
//	    }
//          
//	    grp_it = data.groups.find(i);
//	    if (grp_it != data.groups.end()) {
//	      g.group(counts);
//	      g2.group(counts);
//	    }
//
//	    g.saveState(buf1);
//	    g2.saveState(buf2);
//          
//	    TEST(buf1.str() == buf2.str());
//	  }
//
//	} // end checkpointing and resuming
//        
//      } // for (UInt modeIdx = 0; modeIdx < numModes; modeIdx++)
//      
//    } // for (Size n = 0; n < tcs.size(); ++n)
//    
//  } // GrouperUnitTest::unitTestSaveReadState
// 
  //--------------------------------------------------------------------------------
  void GrouperUnitTest::RunTests()
  {
    // test TBI
    //testTBI();
    //
    //// Test learning and grouping
    //doOneTestCase("0");
    //doOneTestCase("1");
    //doOneTestCase("2");
    //doOneTestCase("3");
    //doOneTestCase("4");
    //doOneTestCase("5");
    //doOneTestCase("6");
    //doOneTestCase("7");
    //doOneTestCase("8");
    //
    //// Test save and read state
    //testSaveReadState();
  }
    
  //--------------------------------------------------------------------------------
} // end namespace nta


