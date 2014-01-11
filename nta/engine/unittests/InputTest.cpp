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
 * Implementation of Input test
 */

#include <nta/engine/unittests/InputTest.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Network.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Output.hpp>

using namespace nta;

void InputTest::RunTests()
{
  {
    Network net;
    Region * r1 = net.addRegion("r1", "TestNode", "");
    Region * r2 = net.addRegion("r2", "TestNode", "");

    //Test constructor
    Input x(*r1, NTA_BasicType_Int32, true);
    Input y(*r2, NTA_BasicType_Byte, false);
    Region * rn = NULL;
    SHOULDFAIL(Input z(*rn, NTA_BasicType_Int32, true));
    SHOULDFAIL(Input i(*r1, (NTA_BasicType)(NTA_BasicType_Last + 1), true));

    //test getRegion()
    TESTEQUAL(r1, &(x.getRegion()));
    TESTEQUAL(r2, &(y.getRegion()));
    
    //test isRegionLevel()
    TEST(x.isRegionLevel());
    TEST(! y.isRegionLevel());

    //test isInitialized()
    TEST(! x.isInitialized());
    TEST(! y.isInitialized());

    //test one case of initialize()
    SHOULDFAIL(x.initialize());
    SHOULDFAIL(y.initialize());

    Dimensions d1;
    d1.push_back(8);
    d1.push_back(4);
    r1->setDimensions(d1);
    Dimensions d2;
    d2.push_back(4);
    d2.push_back(2);
    r2->setDimensions(d2);
    net.link("r1", "r2", "TestFanIn2", "");

    x.initialize();
    y.initialize();

    //test evaluateLinks()
    //should return 0 because x is initialized
    TESTEQUAL(0u, x.evaluateLinks());
    //should return 0 because there are no links
    TESTEQUAL(0u, y.evaluateLinks());

    //test getData()
    const ArrayBase * pa = &(y.getData());
    TESTEQUAL(0u, pa->getCount());
    Real64* buf = (Real64*)(pa->getBuffer());
    TEST(buf != NULL);
  }

  {
    Network net;
    Region * region1 = net.addRegion("region1", "TestNode", "");
    Region * region2 = net.addRegion("region2", "TestNode", "");

    Dimensions d1;
    d1.push_back(8);
    d1.push_back(4);
    region1->setDimensions(d1);

    net.link("region1", "region2", "TestFanIn2", "");

    //test initialize(), which is called by net.initialize()
    //also test evaluateLinks() which is called here
    net.initialize();
    net.run(1);

    //test that region has correct induced dimensions
    Dimensions d2 = region2->getDimensions();
    TESTEQUAL(2u, d2.size());
    TESTEQUAL(4u, d2[0]);
    TESTEQUAL(2u, d2[1]);

    //test getName() and setName()
    Input * in1 = region1->getInput("bottomUpIn");
    Input * in2 = region2->getInput("bottomUpIn");

    TESTEQUAL("bottomUpIn", in1->getName());
    TESTEQUAL("bottomUpIn", in2->getName());
    in1->setName("uselessName");
    TESTEQUAL("uselessName", in1->getName());
    in1->setName("bottomUpIn");

    //test isInitialized()
    TEST(in1->isInitialized());
    TEST(in2->isInitialized());

    //test getLinks()
    std::vector<Link*> links = in2->getLinks();
    TESTEQUAL(1u, links.size());
    for(unsigned int i=0; i<links.size(); i++) {
      //do something to make sure l[i] is a valid Link*
      TEST(links[i] != NULL);
      //should fail because regions are initialized
      SHOULDFAIL(in2->removeLink(links[i]));
    }

    //test findLink()
    Link * l1 = in1->findLink("region1", "bottomUpOut");
    TEST(l1 == NULL);
    Link * l2 = in2->findLink("region1", "bottomUpOut");
    TEST(l2 != NULL);


    //test removeLink(), uninitialize()
    //uninitialize() is called internally from removeLink()
    {
      //can't remove link b/c region1 initialized
      SHOULDFAIL(in2->removeLink(l2)); 
      //can't remove region b/c region1 has links
      SHOULDFAIL(net.removeRegion("region1")); 
      region1->uninitialize();
      region2->uninitialize();
      SHOULDFAIL(in1->removeLink(l2));
      in2->removeLink(l2);
      SHOULDFAIL(in2->removeLink(l2));
      //l1 == NULL
      SHOULDFAIL(in1->removeLink(l1));
    }
  }

  {
    Network net;
    Region * region1 = net.addRegion("region1", "TestNode", "");
    Region * region2 = net.addRegion("region2", "TestNode", "");

    Dimensions d1;
    d1.push_back(8);
    d1.push_back(4);
    region1->setDimensions(d1);

    //test addLink() indirectly - it is called by Network::link()
    net.link("region1", "region2", "TestFanIn2", "");

    //test initialize(), which is called by net.initialize()
    net.initialize();

    Dimensions d2 = region2->getDimensions();
    Input * in1 = region1->getInput("bottomUpIn");
    Input * in2 = region2->getInput("bottomUpIn");
    Output * out1 = region1->getOutput("bottomUpOut");
    
    //test isInitialized()
    TEST(in1->isInitialized());
    TEST(in2->isInitialized());

    //test evaluateLinks(), in1 already initialized
    TESTEQUAL(0u, in1->evaluateLinks());
    TESTEQUAL(0u, in2->evaluateLinks());

    //test prepare
    {    
      //set in2 to all zeroes
      const ArrayBase * ai2 = &(in2->getData());
      Real64* idata = (Real64*)(ai2->getBuffer());
      for (UInt i = 0; i < 64; i++)
        idata[i] = 0;

      //set out1 to all 10's
      const ArrayBase * ao1 = &(out1->getData());
      idata = (Real64*)(ao1->getBuffer());
      for (UInt i = 0; i < 64; i++)
        idata[i] = 10;

      //confirm that in2 is still all zeroes
      ai2 = &(in2->getData());
      idata = (Real64*)(ai2->getBuffer());
      //only test 4 instead of 64 to cut down on number of tests
      for (UInt i = 0; i < 4; i++)
        TESTEQUAL(0, idata[i]);

      in2->prepare();

      //confirm that in2 is now all 10's
      ai2 = &(in2->getData());
      idata = (Real64*)(ai2->getBuffer());
      //only test 4 instead of 64 to cut down on number of tests
      for (UInt i = 0; i < 4; i++)
        TESTEQUAL(10, idata[i]);
    }

    net.run(2);

    //test getSplitterMap()
    std::vector< std::vector<size_t> > sm;
    sm = in2->getSplitterMap();
    TESTEQUAL(8u, sm.size());
    TESTEQUAL(8u, sm[0].size());
    TESTEQUAL(16u, sm[0][4]);
    TESTEQUAL(12u, sm[3][0]);
    TESTEQUAL(31u, sm[3][7]);
   
    //test getInputForNode()
    std::vector<Real64> input;
    in2->getInputForNode(0, input);
    TESTEQUAL(1, input[0]);
    TESTEQUAL(0, input[1]);
    TESTEQUAL(8, input[5]);
    TESTEQUAL(9, input[7]);
    in2->getInputForNode(3, input);
    TESTEQUAL(1, input[0]);
    TESTEQUAL(6, input[1]);
    TESTEQUAL(15, input[7]);
    
    //test getData()
    const ArrayBase * pa = &(in2->getData());
    TESTEQUAL(64u, pa->getCount());
    Real64* data = (Real64*)(pa->getBuffer());
    TESTEQUAL(1, data[0]);
    TESTEQUAL(0, data[1]);
    TESTEQUAL(1, data[30]);
    TESTEQUAL(15, data[31]);
    TESTEQUAL(31, data[63]);
  }

  //test with two regions linking into the same input
  {
    Network net;
    Region * region1 = net.addRegion("region1", "TestNode", "");
    Region * region2 = net.addRegion("region2", "TestNode", "");
    Region * region3 = net.addRegion("region3", "TestNode", "");

    Dimensions d1;
    d1.push_back(8);
    d1.push_back(4);
    region1->setDimensions(d1);
    region2->setDimensions(d1);

    net.link("region1", "region3", "TestFanIn2", "");
    net.link("region2", "region3", "TestFanIn2", "");

    net.initialize();
    
    Dimensions d3 = region3->getDimensions();
    Input * in3 = region3->getInput("bottomUpIn");
    
    TESTEQUAL(2u, d3.size());
    TESTEQUAL(4u, d3[0]);
    TESTEQUAL(2u, d3[1]);

    net.run(2);
    
    //test getSplitterMap()
    std::vector< std::vector<size_t> > sm;
    sm = in3->getSplitterMap();
    TESTEQUAL(8u, sm.size());
    TESTEQUAL(16u, sm[0].size());
    TESTEQUAL(16u, sm[0][4]);
    TESTEQUAL(12u, sm[3][0]);
    TESTEQUAL(31u, sm[3][7]);
    
    //test getInputForNode()
    std::vector<Real64> input;
    in3->getInputForNode(0, input);
    TESTEQUAL(1, input[0]);
    TESTEQUAL(0, input[1]);
    TESTEQUAL(8, input[5]);
    TESTEQUAL(9, input[7]);
    in3->getInputForNode(3, input);
    TESTEQUAL(1, input[0]);
    TESTEQUAL(6, input[1]);
    TESTEQUAL(15, input[7]);
    
    //test getData()
    const ArrayBase * pa = &(in3->getData());
    TESTEQUAL(128u, pa->getCount());
    Real64* data = (Real64*)(pa->getBuffer());
    TESTEQUAL(1, data[0]);
    TESTEQUAL(0, data[1]);
    TESTEQUAL(1, data[30]);
    TESTEQUAL(15, data[31]);
    TESTEQUAL(31, data[63]);
    TESTEQUAL(1, data[64]);
    TESTEQUAL(0, data[65]);
    TESTEQUAL(1, data[94]);
    TESTEQUAL(15, data[95]);
    TESTEQUAL(31, data[127]);
    
  }

}
