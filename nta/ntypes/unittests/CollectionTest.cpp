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
 * Implementation of Collection test
 */

#include "CollectionTest.hpp"
#include <nta/ntypes/Collection.hpp>
#include <sstream>
#include <algorithm>

// Collection implementation needed for explicit instantiation
#include <nta/ntypes/Collection.cpp>

namespace nta
{
  struct Item
  {
    int x;

    Item() : x(-1)
    {
    }

    Item(int x) : x(x)
    {
    }
  };

  // The Collection class must be explicitly instantiated. 
  template class Collection<int>;
  template class Collection<Item>;
  template class Collection<Item*>;

  void CollectionTest::testEmptyCollection()
  {
    Collection<int> c;
    TEST(c.getCount() == 0);
    TEST(c.contains("blah") == false);
    SHOULDFAIL(c.getByIndex(0));
    SHOULDFAIL(c.getByName("blah"));
  }

  void CollectionTest::testCollectionWith_1_Item()
  {
    Item * p = new Item(5);
    Collection<Item *> c;
    TEST(c.contains("x") == false);
    c.add("x", p);
    TEST(c.contains("x") == true);
    TEST(c.getCount() == 1);
    TEST(c.getByIndex(0).second->x == 5);
    TEST(c.getByName("x")->x == 5);
    
    SHOULDFAIL(c.getByIndex(1));
    SHOULDFAIL(c.getByName("blah"));

    delete p;
  }

  void CollectionTest::testCollectionWith_2_Items()
  {
    Collection<Item> c;
    c.add("x1", Item(1));
    c.add("x2", Item(2));
    TEST(c.getCount() == 2);

    Item i1 = c.getByIndex(0).second;
    Item i2 = c.getByIndex(1).second;

    TEST(i1.x == 1 && i2.x == 2);

    TEST(c.contains("no such item") == false);
    TEST(c.contains("x1") == true);
      TEST(c.contains("x2") == true);
    TEST(c.getByName("x1").x == 1);
    TEST(c.getByName("x2").x == 2);
    
    SHOULDFAIL(c.getByIndex(2));
    SHOULDFAIL(c.getByName("blah"));    
  }


  void CollectionTest::testCollectionWith_137_Items()
  {
    Collection<int> c;
    for (int i = 0; i < 137; ++i)
    {
      std::stringstream ss;
      ss << i;
      c.add(ss.str(), i);
    }

    TEST(c.getCount() == 137);

    for (int i = 0; i < 137; ++i)
    {
      TEST(c.getByIndex(i).second == i);
    }

    SHOULDFAIL(c.getByIndex(137));
    SHOULDFAIL(c.getByName("blah"));    
  }

  void CollectionTest::testCollectionAddRemove()
  {
    Collection<int> c;
    c.add("0", 0);
    c.add("1", 1);
    c.add("2", 2);
    // c is now: 0,1,2
    TEST(c.contains("0"));
    TEST(c.contains("1"));
    TEST(c.contains("2"));
    TEST(!c.contains("3"));
      
    SHOULDFAIL(c.add("0", 0));
    SHOULDFAIL(c.add("1", 1));
    SHOULDFAIL(c.add("2", 2));

    TESTEQUAL(0, c.getByName("0"));
    TESTEQUAL(1, c.getByName("1"));
    TESTEQUAL(2, c.getByName("2"));

    TESTEQUAL(0, c.getByIndex(0).second);
    TESTEQUAL(1, c.getByIndex(1).second);
    TESTEQUAL(2, c.getByIndex(2).second);

    TEST(c.getCount() == 3);

    SHOULDFAIL(c.remove("4"));

    // remove in middle of collection
    c.remove("1");
    // c is now 0, 2
    SHOULDFAIL(c.remove("1"));
    
    TEST(c.getCount() == 2);
    TEST(c.contains("0"));
    TEST(!c.contains("1"));
    TEST(c.contains("2"));

    TESTEQUAL(0, c.getByIndex(0).second);
    // item "2" has shifted into position 1
    TESTEQUAL(2, c.getByIndex(1).second);
    
    // should append to end of collection
    c.add("1", 1);
    // c is now 0, 2, 1
    TEST(c.getCount() == 3);
    TEST(c.contains("1"));
    TESTEQUAL(0, c.getByIndex(0).second);
    TESTEQUAL(2, c.getByIndex(1).second);
    TESTEQUAL(1, c.getByIndex(2).second);

    SHOULDFAIL(c.add("0", 0));
    SHOULDFAIL(c.add("1", 1));
    SHOULDFAIL(c.add("2", 2));

    // remove at end of collection
    c.remove("1");
    // c is now 0, 2
    SHOULDFAIL(c.remove("1"));
    TEST(c.getCount() == 2);
    TESTEQUAL(0, c.getByIndex(0).second);
    TESTEQUAL(2, c.getByIndex(1).second);

    // continue removing until done
    c.remove("0");
    // c is now 2
    SHOULDFAIL(c.remove("0"));
    TEST(c.getCount() == 1);
    // "2" shifts to first position
    TESTEQUAL(2, c.getByIndex(0).second);

    c.remove("2");
    // c is now empty
    TEST(c.getCount() == 0);
    TEST(!c.contains("2"));

  }



  void CollectionTest::RunTests()
  {
    testEmptyCollection();
    testCollectionWith_1_Item();
    testCollectionWith_2_Items();
    testCollectionWith_137_Items();
    testCollectionAddRemove();
  }
}

