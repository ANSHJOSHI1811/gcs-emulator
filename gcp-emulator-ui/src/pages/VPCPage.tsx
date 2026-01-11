import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listNetworks, listAllSubnetworks, Network, Subnetwork } from '../api/vpc';

interface NetworkWithSubnets extends Network {
  subnetCount: number;
  regions: string[];
}

const VPCPage: React.FC = () => {
  const navigate = useNavigate();
  const [networks, setNetworks] = useState<NetworkWithSubnets[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNetworks();
  }, []);

  const loadNetworks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [networksList, allSubnets] = await Promise.all([
        listNetworks(),
        listAllSubnetworks()
      ]);

      // Enrich networks with subnet data
      const enrichedNetworks: NetworkWithSubnets[] = networksList.map(network => {
        const networkSubnets = allSubnets.filter(subnet => 
          subnet.network.includes(network.name)
        );
        
        const regions = Array.from(new Set(networkSubnets.map(s => s.region)));
        
        return {
          ...network,
          subnetCount: networkSubnets.length,
          regions
        };
      });

      setNetworks(enrichedNetworks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load VPC networks');
      console.error('Failed to load networks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNetworkClick = (networkName: string) => {
    navigate(`/vpc/${networkName}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading VPC networks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
          <button
            onClick={loadNetworks}
            className="mt-2 text-sm underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">VPC Networks</h1>
            <p className="mt-2 text-gray-600">
              Virtual Private Cloud networks and subnetworks (Control Plane - Phase 1)
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            ← Back to Services
          </button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              <strong>Phase 1 Control Plane:</strong> Networks and subnets provide identity only. 
              No real networking, routing, or security groups. IPs are fake and assigned sequentially.
            </p>
          </div>
        </div>
      </div>

      {/* Networks Table */}
      {networks.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No VPC networks</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create a compute instance to automatically create the default network.
          </p>
          <button
            onClick={() => navigate('/compute')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Compute Engine
          </button>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Network Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mode
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subnets
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Regions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Routing Mode
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {networks.map((network) => (
                <tr
                  key={network.id}
                  onClick={() => handleNetworkClick(network.name)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {network.name}
                        </div>
                        {network.description && (
                          <div className="text-sm text-gray-500">
                            {network.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      network.autoCreateSubnetworks
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {network.autoCreateSubnetworks ? 'Auto' : 'Custom'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {network.subnetCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {network.regions.length > 0 ? (
                      <span>{network.regions.length} region{network.regions.length !== 1 ? 's' : ''}</span>
                    ) : (
                      <span className="text-gray-400">No subnets</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {network.routingConfig.routingMode}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer Info */}
      {networks.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          <p>
            Click on a network to view its subnets and IP allocation details.
          </p>
        </div>
      )}
    </div>
  );
};

export default VPCPage;
