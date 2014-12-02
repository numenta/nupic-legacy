

namespace nupic
{
	using System;
	
	public class Network : net_internal.Network 
	{

		public Network()
		{
		}
		
		/// <summary>
		/// 
		/// </summary>
		public uint RegionCount
		{
			get { return this.getRegionCount(); }
		}
	}
}
