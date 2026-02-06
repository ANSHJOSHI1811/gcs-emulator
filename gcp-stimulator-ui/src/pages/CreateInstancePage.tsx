import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { apiClient } from '../api/client';
import { Cpu, ArrowLeft, Loader2, AlertCircle, CheckCircle, Plus, X } from 'lucide-react';

const OS_IMAGES = [
  { value: 'debian-11', label: 'Debian GNU/Linux 11 (bullseye)', description: 'Stable and popular Linux distribution' },
  { value: 'ubuntu-2204-lts', label: 'Ubuntu 22.04 LTS', description: 'Long-term support Ubuntu release' },
  { value: 'ubuntu-2004-lts', label: 'Ubuntu 20.04 LTS', description: 'Previous LTS version' },
  { value: 'centos-stream-9', label: 'CentOS Stream 9', description: 'Rolling release of RHEL' },
  { value: 'rocky-linux-9', label: 'Rocky Linux 9', description: 'RHEL-compatible distribution' },
  { value: 'windows-server-2022', label: 'Windows Server 2022', description: 'Latest Windows Server' },
  { value: 'windows-server-2019', label: 'Windows Server 2019', description: 'Previous Windows Server' },
];

interface Zone {
  name: string;
  region: string;
  status: string;
}

interface Network {
  name: string;
  selfLink: string;
  autoCreateSubnetworks: boolean;
  IPv4Range?: string;
}

interface Subnet {
  name: string;
  network: string;
  region: string;
  ipCidrRange: string;
}

export default function CreateInstancePage() {
  const navigate = useNavigate();
  const { currentProject } = useProject();
  
  const [formData, setFormData] = useState({
    name: '',
    zone: '',
    machineType: 'e2-micro',
    sourceImage: 'debian-11',
    network: '',
    subnetwork: '',
  });

  const [zones, setZones] = useState<Zone[]>([]);
  const [networks, setNetworks] = useState<Network[]>([]);
  const [subnets, setSubnets] = useState<Subnet[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSubnetForm, setShowSubnetForm] = useState(false);
  const [creatingSubnet, setCreatingSubnet] = useState(false);
  const [subnetFormData, setSubnetFormData] = useState({
    name: '',
    ipCidrRange: '',
  });

  useEffect(() => {
    loadData();
  }, [currentProject]);

  const loadData = async () => {
    if (!currentProject) return;
    
    try {
      setLoading(true);
      setError(null);

      // Load zones
      const zonesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/zones`);
      const zonesList = zonesRes.data.items || [];
      setZones(zonesList);

      // Load networks
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      const networksList = networksRes.data.items || [];
      setNetworks(networksList);

      // Load subnets
      const subnetsRes = await apiClient.get(`/compute/v1/projects/${currentProject}/aggregated/subnetworks`);
      const allSubnets: Subnet[] = [];
      if (subnetsRes.data.items) {
        Object.values<any>(subnetsRes.data.items).forEach((item: any) => {
          if (item.subnetworks) {
            allSubnets.push(...item.subnetworks);
          }
        });
      }
      setSubnets(allSubnets);

      // Set default values if available
      if (zonesList.length > 0 && !formData.zone) {
        setFormData(prev => ({ ...prev, zone: zonesList[0].name }));
      }
      if (networksList.length > 0 && !formData.network) {
        const defaultNetwork = networksList.find((n: Network) => n.name === 'default') || networksList[0];
        setFormData(prev => ({ ...prev, network: defaultNetwork.name }));
      }
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError('Failed to load resources. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const extractResourceName = (url: string) => {
    const parts = url.split('/');
    return parts[parts.length - 1];
  };

  const filteredSubnets = subnets.filter(subnet => {
    const selectedZone = zones.find(z => z.name === formData.zone);
    const subnetRegion = extractResourceName(subnet.region);
    const selectedRegion = selectedZone?.region;
    const networkName = extractResourceName(subnet.network);
    
    // Debug logging
    if (formData.network && formData.zone) {
      console.log('Filtering subnet:', {
        subnetName: subnet.name,
        subnetNetwork: subnet.network,
        extractedNetwork: networkName,
        selectedNetwork: formData.network,
        networkMatch: networkName === formData.network,
        subnetRegion: subnet.region,
        extractedRegion: subnetRegion,
        selectedRegion: selectedRegion,
        regionMatch: subnetRegion === selectedRegion
      });
    }
    
    return (
      networkName === formData.network &&
      subnetRegion === selectedRegion
    );
  });

  const handleCreateSubnet = async () => {
    if (!currentProject || !formData.zone || !formData.network) return;
    if (!subnetFormData.name || !subnetFormData.ipCidrRange) return;

    try {
      setCreatingSubnet(true);
      setError(null);

      const selectedZone = zones.find(z => z.name === formData.zone);
      const region = selectedZone?.region;

      if (!region) {
        setError('Please select a zone first');
        setCreatingSubnet(false);
        return;
      }

      // Validate CIDR format
      const cidrRegex = /^([0-9]{1,3}\.){3}[0-9]{1,3}\/([0-9]|[1-2][0-9]|3[0-2])$/;
      if (!cidrRegex.test(subnetFormData.ipCidrRange)) {
        setError('Invalid IP CIDR format. Use format like 10.0.1.0/24');
        setCreatingSubnet(false);
        return;
      }

      // Validate subnet name (GCP requirements: 1-63 chars, lowercase, numbers, hyphens)
      const nameRegex = /^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$/;
      if (!nameRegex.test(subnetFormData.name)) {
        setError('Subnet name must start with a letter, be 1-63 characters, and contain only lowercase letters, numbers, and hyphens');
        setCreatingSubnet(false);
        return;
      }

      await apiClient.post(
        `/compute/v1/projects/${currentProject}/regions/${region}/subnetworks`,
        {
          name: subnetFormData.name,
          network: formData.network,  // Just the network name, not full URL
          ipCidrRange: subnetFormData.ipCidrRange,
        }
      );

      // Reload subnets
      const subnetsRes = await apiClient.get(`/compute/v1/projects/${currentProject}/aggregated/subnetworks`);
      const allSubnets: Subnet[] = [];
      if (subnetsRes.data.items) {
        Object.values<any>(subnetsRes.data.items).forEach((item: any) => {
          if (item.subnetworks) {
            allSubnets.push(...item.subnetworks);
          }
        });
      }
      setSubnets(allSubnets);

      // Auto-select the newly created subnet
      setFormData(prev => ({ ...prev, subnetwork: subnetFormData.name }));

      // Reset form and hide it
      setSubnetFormData({ name: '', ipCidrRange: '' });
      setShowSubnetForm(false);
    } catch (err: any) {
      console.error('Failed to create subnet:', err);
      setError(err.response?.data?.error?.message || 'Failed to create subnet. Please try again.');
    } finally {
      setCreatingSubnet(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;

    try {
      setCreating(true);
      setError(null);

      // GCP Validation: Instance name must be 1-63 characters, start with letter, lowercase, hyphens allowed
      const nameRegex = /^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$/;
      if (!nameRegex.test(formData.name)) {
        setError('Instance name must start with a letter, be 1-63 characters, and contain only lowercase letters, numbers, and hyphens (cannot end with hyphen)');
        setCreating(false);
        return;
      }

      // Validate required fields
      if (!formData.zone) {
        setError('Please select a zone');
        setCreating(false);
        return;
      }

      if (!formData.network) {
        setError('Please select a network');
        setCreating(false);
        return;
      }

      if (filteredSubnets.length > 0 && !formData.subnetwork) {
        setError('Please select a subnet');
        setCreating(false);
        return;
      }

      const payload = {
        name: formData.name,
        machineType: `zones/${formData.zone}/machineTypes/${formData.machineType}`,
        disks: [
          {
            boot: true,
            autoDelete: true,
            initializeParams: {
              sourceImage: `projects/debian-cloud/global/images/${formData.sourceImage}`,
              diskSizeGb: '10',
            },
          },
        ],
        networkInterfaces: [
          {
            network: `projects/${currentProject}/global/networks/${formData.network}`,
            subnetwork: formData.subnetwork
              ? `projects/${currentProject}/regions/${zones.find(z => z.name === formData.zone)?.region}/subnetworks/${formData.subnetwork}`
              : undefined,
          },
        ],
      };

      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${formData.zone}/instances`,
        payload
      );

      // Navigate back to instances page
      navigate('/services/compute-engine/instances');
    } catch (err: any) {
      console.error('Failed to create instance:', err);
      setError(err.response?.data?.error?.message || 'Failed to create instance. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading resources...</p>
        </div>
      </div>
    );
  }

  const selectedZone = zones.find(z => z.name === formData.zone);
  const selectedImage = OS_IMAGES.find(img => img.value === formData.sourceImage);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-8 py-6">
          <Link
            to="/services/compute-engine/instances"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4 text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Instances
          </Link>
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Cpu className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Create VM Instance</h1>
              <p className="text-gray-600 mt-1">Deploy a new virtual machine in {currentProject}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Instance Details Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Instance Details</h2>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value.toLowerCase() })}
                  placeholder="my-instance"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="mt-1.5 text-xs text-gray-500">
                  Must start with a letter, 1-63 characters, lowercase letters, numbers, and hyphens only
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs text-blue-900">
                  <strong>💡 GCP Best Practices:</strong> Use descriptive names like <code className="bg-blue-100 px-1 py-0.5 rounded">web-server-prod</code>, <code className="bg-blue-100 px-1 py-0.5 rounded">db-primary</code>, or <code className="bg-blue-100 px-1 py-0.5 rounded">app-backend-01</code>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Region <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={selectedZone?.region || ''}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                  />
                  <p className="mt-1.5 text-xs text-gray-500">Set by zone selection</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Zone <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    value={formData.zone}
                    onChange={(e) => setFormData({ ...formData, zone: e.target.value, subnetwork: '' })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select zone</option>
                    {zones.map(zone => (
                      <option key={zone.name} value={zone.name}>
                        {zone.name}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-xs text-gray-500">{zones.length} zone(s) available</p>
                </div>
              </div>
            </div>
          </div>

          {/* Machine Configuration Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Machine Configuration</h2>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Machine Type <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.machineType}
                  onChange={(e) => setFormData({ ...formData, machineType: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <optgroup label="E2 Series (Cost-optimized)">
                    <option value="e2-micro">e2-micro (2 vCPUs, 1 GB RAM)</option>
                    <option value="e2-small">e2-small (2 vCPUs, 2 GB RAM)</option>
                    <option value="e2-medium">e2-medium (2 vCPUs, 4 GB RAM)</option>
                  </optgroup>
                  <optgroup label="N1 Series (Balanced)">
                    <option value="n1-standard-1">n1-standard-1 (1 vCPU, 3.75 GB RAM)</option>
                    <option value="n1-standard-2">n1-standard-2 (2 vCPUs, 7.5 GB RAM)</option>
                    <option value="n1-standard-4">n1-standard-4 (4 vCPUs, 15 GB RAM)</option>
                  </optgroup>
                </select>
              </div>
            </div>
          </div>

          {/* Boot Disk Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Boot Disk</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Operating System <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.sourceImage}
                  onChange={(e) => setFormData({ ...formData, sourceImage: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <optgroup label="Linux">
                    <option value="debian-11">Debian GNU/Linux 11 (bullseye)</option>
                    <option value="ubuntu-2204-lts">Ubuntu 22.04 LTS</option>
                    <option value="ubuntu-2004-lts">Ubuntu 20.04 LTS</option>
                    <option value="centos-stream-9">CentOS Stream 9</option>
                    <option value="rocky-linux-9">Rocky Linux 9</option>
                  </optgroup>
                  <optgroup label="Windows">
                    <option value="windows-server-2022">Windows Server 2022</option>
                    <option value="windows-server-2019">Windows Server 2019</option>
                  </optgroup>
                </select>
              </div>
              
              {selectedImage && (
                <div className="bg-gradient-to-r from-gray-50 to-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{selectedImage.label}</p>
                      <p className="text-xs text-gray-600 mt-1">{selectedImage.description}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs text-blue-900">
                  <strong>💡 Note:</strong> A Docker container will be automatically created to simulate this VM instance.
                </p>
              </div>
            </div>
          </div>

          {/* Networking Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Networking</h2>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Network <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.network}
                  onChange={(e) => setFormData({ ...formData, network: e.target.value, subnetwork: '' })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select network</option>
                  {networks.map(network => (
                    <option key={network.name} value={network.name}>
                      {network.name}
                    </option>
                  ))}
                </select>
              </div>

              {formData.network && filteredSubnets.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Subnet <span className="text-red-500">*</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowSubnetForm(!showSubnetForm)}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" />
                      Create new subnet
                    </button>
                  </div>
                  <select
                    required
                    value={formData.subnetwork}
                    onChange={(e) => setFormData({ ...formData, subnetwork: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select subnet</option>
                    {filteredSubnets.map(subnet => (
                      <option key={subnet.name} value={subnet.name}>
                        {subnet.name} ({subnet.ipCidrRange})
                      </option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-xs text-gray-500">
                    {filteredSubnets.length} subnet(s) available in {selectedZone?.region} (Total loaded: {subnets.length})
                  </p>
                </div>
              )}

              {formData.network && filteredSubnets.length === 0 && !showSubnetForm && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-yellow-900">No subnets available</p>
                      <p className="text-xs text-yellow-700 mt-1">
                        Create a subnet in the selected network and region to continue.
                      </p>
                      <button
                        type="button"
                        onClick={() => setShowSubnetForm(true)}
                        className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
                      >
                        <Plus className="w-4 h-4" />
                        Create Subnet Now
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Inline Subnet Creation Form */}
              {formData.network && showSubnetForm && (
                <div className="mt-4 border-2 border-blue-200 rounded-lg p-5 bg-blue-50">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                      <Plus className="w-4 h-4 text-blue-600" />
                      Create New Subnet
                    </h3>
                    <button
                      type="button"
                      onClick={() => {
                        setShowSubnetForm(false);
                        setSubnetFormData({ name: '', ipCidrRange: '' });
                        setError(null);
                      }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Subnet Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={subnetFormData.name}
                        onChange={(e) => setSubnetFormData({ ...subnetFormData, name: e.target.value })}
                        placeholder="my-subnet"
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      <p className="mt-1.5 text-xs text-gray-500">Start with a letter, 1-63 chars, lowercase letters, numbers, and hyphens</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        IP CIDR Range <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={subnetFormData.ipCidrRange}
                        onChange={(e) => setSubnetFormData({ ...subnetFormData, ipCidrRange: e.target.value })}
                        placeholder="10.128.1.0/24"
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      <p className="mt-1.5 text-xs text-gray-500">
                        Network: <strong>{formData.network}</strong> ({networks.find(n => n.name === formData.network)?.IPv4Range || '10.128.0.0/9'}) • Region: <strong>{selectedZone?.region}</strong>
                      </p>
                      <p className="mt-1 text-xs text-red-600 font-semibold">
                        ⚠️ Subnet CIDR must be within VPC range and NOT overlap with existing subnets
                      </p>
                    </div>

                    <div className="bg-amber-50 border border-amber-300 rounded-lg p-3">
                      <p className="text-xs text-amber-900">
                        <strong className="text-red-700">❌ WRONG:</strong> Using same CIDR (10.0.0.0/24) for multiple subnets - causes IP conflicts!<br/>
                        <strong className="text-green-700 mt-2 block">✅ CORRECT:</strong> Use non-overlapping CIDRs within VPC range:<br/>
                        • <code className="bg-amber-200 px-1 py-0.5 rounded">10.0.0.0/24</code> (256 IPs: 10.0.0.0 → 10.0.0.255)<br/>
                        • <code className="bg-amber-200 px-1 py-0.5 rounded">10.0.1.0/24</code> (256 IPs: 10.0.1.0 → 10.0.1.255)<br/>
                        • <code className="bg-amber-200 px-1 py-0.5 rounded">10.0.2.0/24</code> (256 IPs: 10.0.2.0 → 10.0.2.255)<br/>
                        • <code className="bg-amber-200 px-1 py-0.5 rounded">10.0.4.0/22</code> (1024 IPs: 10.0.4.0 → 10.0.7.255)
                      </p>
                    </div>

                    <div className="flex items-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={handleCreateSubnet}
                        disabled={creatingSubnet || !subnetFormData.name || !subnetFormData.ipCidrRange}
                        className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                      >
                        {creatingSubnet ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          <>
                            <Plus className="w-4 h-4" />
                            Create Subnet
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSubnetForm(false);
                          setSubnetFormData({ name: '', ipCidrRange: '' });
                          setError(null);
                        }}
                        disabled={creatingSubnet}
                        className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => navigate('/services/compute-engine/instances')}
              disabled={creating}
              className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating || !formData.name || !formData.zone || !formData.network || (filteredSubnets.length > 0 && !formData.subnetwork)}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
            >
              {creating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Instance'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
