import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getNetwork, listAllSubnetworks, Network, Subnetwork } from '../api/vpc';

const VPCDetailPage: React.FC = () => {
  const { networkName } = useParams<{ networkName: string }>();
  const navigate = useNavigate();
  const [network, setNetwork] = useState<Network | null>(null);
  const [subnets, setSubnets] = useState<Subnetwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (networkName) {
      loadNetworkDetails();
    }
  }, [networkName]);

  const loadNetworkDetails = async () => {
    if (!networkName) return;

    try {
      setLoading(true);
      setError(null);

      const [networkData, allSubnets] = await Promise.all([
        getNetwork('test-project', networkName),
        listAllSubnetworks()
      ]);

      setNetwork(networkData);

      // Filter subnets for this network
      const networkSubnets = allSubnets.filter(subnet =>
        subnet.network.includes(networkName)
      );
      setSubnets(networkSubnets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load network details');
      console.error('Failed to load network details:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading network details...</p>
        </div>
      </div>
    );
  }

  if (error || !network) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error || 'Network not found'}</p>
          <button
            onClick={() => navigate('/vpc')}
            className="mt-2 text-sm underline hover:no-underline"
          >
            ← Back to VPC Networks
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
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => navigate('/vpc')}
                className="text-gray-600 hover:text-gray-900"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-3xl font-bold text-gray-900">{network.name}</h1>
              <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                network.autoCreateSubnetworks
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {network.autoCreateSubnetworks ? 'Auto Mode' : 'Custom Mode'}
              </span>
            </div>
            {network.description && (
              <p className="text-gray-600">{network.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Network Details Card */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Network Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Network ID</dt>
            <dd className="mt-1 text-sm text-gray-900 font-mono">{network.id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Routing Mode</dt>
            <dd className="mt-1 text-sm text-gray-900">{network.routingConfig.routingMode}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">MTU</dt>
            <dd className="mt-1 text-sm text-gray-900">{network.mtu} bytes</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(network.creationTimestamp).toLocaleString()}
            </dd>
          </div>
          <div className="md:col-span-2">
            <dt className="text-sm font-medium text-gray-500">Self Link</dt>
            <dd className="mt-1 text-sm text-gray-600 font-mono break-all">{network.selfLink}</dd>
          </div>
        </div>
      </div>

      {/* Phase 1 Notice */}
      <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <p className="text-sm text-yellow-800">
              <strong>Phase 1 Control Plane:</strong> This is a logical network only. 
              No real packets flow, no routing occurs, and firewall rules are not enforced. 
              IP addresses are assigned sequentially starting from .2 in each subnet's CIDR range.
            </p>
          </div>
        </div>
      </div>

      {/* Subnets Section */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Subnetworks ({subnets.length})
          </h2>
        </div>

        {subnets.length === 0 ? (
          <div className="text-center py-12">
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
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No subnets</h3>
            <p className="mt-1 text-sm text-gray-500">
              This network doesn't have any subnets yet.
            </p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subnet Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Region
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP CIDR Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gateway
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Private Google Access
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {subnets.map((subnet) => (
                <tr key={subnet.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 bg-purple-100 rounded-lg flex items-center justify-center">
                        <svg className="h-5 w-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm0 2h10v7h-2l-1 2H8l-1-2H5V5z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {subnet.name}
                        </div>
                        {subnet.description && (
                          <div className="text-sm text-gray-500">
                            {subnet.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {subnet.region}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {subnet.ipCidrRange}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                    {subnet.gatewayAddress}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      subnet.privateIpGoogleAccess
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {subnet.privateIpGoogleAccess ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      {subnets.length > 0 && (
        <div className="mt-6 text-sm text-gray-600">
          <p>
            IPs are allocated sequentially starting from the second address in each subnet's CIDR range.
            Phase 1 does not track individual IP allocations or support IP reuse.
          </p>
        </div>
      )}
    </div>
  );
};

export default VPCDetailPage;
