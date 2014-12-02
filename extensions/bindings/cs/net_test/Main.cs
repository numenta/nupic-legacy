using System;
using nupic;

namespace net_test
{
	class MainClass
	{
		public static void Main (string[] args)
		{
			Console.WriteLine("Creating network");
			Network n = new Network();
			Console.WriteLine("Number of regions in network: {0}",
			                  n.getRegionCount());

			Console.WriteLine("Adding level1SP");
			n.addRegion("level1SP", "FDRNode", "");
			
			Console.WriteLine("Number of regions in network: {0}",
			                  n.RegionCount);


			Console.WriteLine("Running for 2 iteraitons");
			n.run(2);
			
			Console.WriteLine ("Done.");
		}
	}

}
