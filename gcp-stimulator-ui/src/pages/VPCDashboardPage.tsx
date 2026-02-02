import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Network, Globe, Lock, Route, TrendingUp } from 'lucide-react';
import { apiClient } from '../api/client';

interface VPCStats {
  networks: number;
  subnets: number;
  firewalls: number;
  routes: number;
}

const VPCDashboardPage = () => {
  const { currentProject } = useProject();
  const [_stats, setStats] = useState<VPCStats>({
    networks: 0,
    subnets: 0,
    firewalls: 0,
    routes: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [currentProject]);

  const loadStats = async () => {
    try {
      const [networksRes, subnetsRes, firewallsRes, routesRes] = await Promise.all([
        apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`).catch(() => ({ data: { items: [] } })),
        apiClient.get(`/compute/v1/projects/${currentProject}/aggregated/subnetworks`).catch(() => ({ data: { items: {} } })),
        apiClient.get(`/compute/v1/projects/${currentProject}/global/firewalls`).catch(() => ({ data: { items: [] } })),
        apiClient.get(`/compute/v1/projects/${currentProject}/global/routes`).catch(() => ({ data: { items: [] } })),
      ]);

      const networks = networksRes.data.items || [];
      const subnetsAgg = subnetsRes.data.items || {};
      const firewalls = firewallsRes.data.items || [];
      const routes = routesRes.data.items || [];

      // Count subnets from aggregated response
      let subnetCount = 0;
      Object.values(subnetsAgg).forEach((regionData: any) => {
        if (regionData.subnetworks) {
          subnetCount += regionData.subnetworks.length;
        }
      });

      setStats({
        networks: networks.length,
        subnets: subnetCount,
        firewalls: firewalls.length,
        routes: routes.length,
      });
    } catch (error) {
      console.error('Failed to load VPC stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading VPC dashboard...</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">VPC Network</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage your Virtual Private Cloud networks, subnets, and connectivity
            </p>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-600">All systems operational</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-8">
        {/* Quick Links */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <a
              href="/services/vpc/networks"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors"
            >
              <Globe className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Create Network</div>
                <div className="text-xs text-gray-500">New VPC network</div>
              </div>
            </a>
            <a
              href="/services/vpc/subnets"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-green-300 transition-colors"
            >
              <Network className="w-5 h-5 text-green-600" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Create Subnet</div>
                <div className="text-xs text-gray-500">Add subnet range</div>
              </div>
            </a>
            <a
              href="/services/vpc/firewalls"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-red-300 transition-colors"
            >
              <Lock className="w-5 h-5 text-red-600" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Add Firewall Rule</div>
                <div className="text-xs text-gray-500">Control traffic</div>
              </div>
            </a>
            <a
              href="/services/vpc/routes"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-purple-300 transition-colors"
            >
              <Route className="w-5 h-5 text-purple-600" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Create Route</div>
                <div className="text-xs text-gray-500">Custom routing</div>
              </div>
            </a>
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">About VPC Networks</h3>
            <p className="text-sm text-gray-600 mb-4">
              Virtual Private Cloud (VPC) provides networking functionality for your cloud resources.
              Each VPC network is a global resource that consists of regional subnets connected by a global
              wide area network.
            </p>
            <ul className="text-sm text-gray-600 space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Create custom networks with your own IP ranges</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Control traffic with firewall rules</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Define custom routes for advanced networking</span>
              </li>
            </ul>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Getting Started</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold">
                  1
                </div>
                <div>
                  <div className="font-medium text-gray-900 text-sm">Create a VPC Network</div>
                  <div className="text-xs text-gray-500">Start with a custom mode network</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold">
                  2
                </div>
                <div>
                  <div className="font-medium text-gray-900 text-sm">Add Subnets</div>
                  <div className="text-xs text-gray-500">Define IP ranges for each region</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold">
                  3
                </div>
                <div>
                  <div className="font-medium text-gray-900 text-sm">Configure Firewall</div>
                  <div className="text-xs text-gray-500">Set up security rules</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VPCDashboardPage;
