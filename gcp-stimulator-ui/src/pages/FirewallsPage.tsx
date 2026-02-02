import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Lock, Plus, Trash2, RefreshCw, AlertCircle, Shield } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';

interface FirewallRule {
  id: string;
  name: string;
  network: string;
  direction: string;
  priority: number;
  action: 'ALLOW' | 'DENY';
  sourceRanges?: string[];
  destinationRanges?: string[];
  sourceTags?: string[];
  targetTags?: string[];
  allowed?: Array<{ IPProtocol: string; ports?: string[] }>;
  denied?: Array<{ IPProtocol: string; ports?: string[] }>;
  disabled?: boolean;
  creationTimestamp?: string;
}

interface NetworkOption {
  name: string;
  selfLink: string;
}

const FirewallsPage = () => {
  const { currentProject } = useProject();
  const [firewalls, setFirewalls] = useState<FirewallRule[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    direction: 'INGRESS',
    action: 'ALLOW' as 'ALLOW' | 'DENY',
    priority: 1000,
    sourceRanges: '0.0.0.0/0',
    protocol: 'tcp',
    ports: '80,443',
    targetTags: '',
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [currentProject]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load networks
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      setNetworks(networksRes.data.items || []);

      // Load firewalls
      const firewallsRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/firewalls`);
      setFirewalls(firewallsRes.data.items || []);
    } catch (error: any) {
      console.error('Failed to load firewalls:', error);
      setError('Failed to load firewalls. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);

    try {
      const sourceRanges = formData.sourceRanges
        .split(',')
        .map(r => r.trim())
        .filter(r => r);

      const ports = formData.ports
        .split(',')
        .map(p => p.trim())
        .filter(p => p);

      const targetTags = formData.targetTags
        .split(',')
        .map(t => t.trim())
        .filter(t => t);

      const ruleData: any = {
        name: formData.name,
        network: formData.network,
        direction: formData.direction,
        priority: formData.priority,
      };

      if (formData.direction === 'INGRESS') {
        ruleData.sourceRanges = sourceRanges.length > 0 ? sourceRanges : ['0.0.0.0/0'];
      } else {
        ruleData.destinationRanges = sourceRanges.length > 0 ? sourceRanges : ['0.0.0.0/0'];
      }

      if (targetTags.length > 0) {
        ruleData.targetTags = targetTags;
      }

      if (formData.action === 'ALLOW') {
        ruleData.allowed = [
          {
            IPProtocol: formData.protocol,
            ...(ports.length > 0 && { ports }),
          },
        ];
      } else {
        ruleData.denied = [
          {
            IPProtocol: formData.protocol,
            ...(ports.length > 0 && { ports }),
          },
        ];
      }

      await apiClient.post(`/compute/v1/projects/${currentProject}/global/firewalls`, ruleData);

      setShowCreateModal(false);
      setFormData({
        name: '',
        network: '',
        direction: 'INGRESS',
        action: 'ALLOW',
        priority: 1000,
        sourceRanges: '0.0.0.0/0',
        protocol: 'tcp',
        ports: '80,443',
        targetTags: '',
      });
      await loadData();
    } catch (error: any) {
      console.error('Failed to create firewall:', error);
      setError(error.response?.data?.error?.message || 'Failed to create firewall rule');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (firewallName: string) => {
    if (!confirm(`Are you sure you want to delete firewall rule "${firewallName}"?`)) {
      return;
    }

    setDeleteLoading(firewallName);
    setError(null);

    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/global/firewalls/${firewallName}`);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete firewall:', error);
      setError(error.response?.data?.error?.message || 'Failed to delete firewall rule');
    } finally {
      setDeleteLoading(null);
    }
  };

  const extractNetworkName = (networkUrl: string): string => {
    if (!networkUrl) return '-';
    const parts = networkUrl.split('/');
    return parts[parts.length - 1] || networkUrl;
  };

  const formatRules = (firewall: FirewallRule): string => {
    const rules = firewall.allowed || firewall.denied || [];
    if (rules.length === 0) return '-';
    
    return rules
      .map(rule => {
        const ports = rule.ports ? `:${rule.ports.join(',')}` : '';
        return `${rule.IPProtocol}${ports}`;
      })
      .join(', ');
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Firewall Rules</h1>
            <p className="text-sm text-gray-500 mt-1">
              Control traffic to and from your VPC networks
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Firewall Rule
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-8 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">Loading firewall rules...</div>
          </div>
        ) : firewalls.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 bg-white rounded-lg border border-gray-200">
            <Lock className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No firewall rules found</h3>
            <p className="text-sm text-gray-500 mb-4">Create your first firewall rule to control traffic</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Firewall Rule
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Network
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Direction
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rules
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {firewalls.map((firewall) => (
                  <tr key={firewall.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Shield className={`w-5 h-5 mr-3 ${firewall.action === 'ALLOW' ? 'text-green-600' : 'text-red-600'}`} />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{firewall.name}</div>
                          <div className="text-xs text-gray-500">{firewall.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{extractNetworkName(firewall.network)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        firewall.action === 'ALLOW'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {firewall.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {firewall.direction}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{firewall.priority}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-mono">{formatRules(firewall)}</div>
                      {firewall.sourceRanges && firewall.sourceRanges.length > 0 && (
                        <div className="text-xs text-gray-500 mt-1">
                          From: {firewall.sourceRanges.join(', ')}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(firewall.name)}
                        disabled={deleteLoading === firewall.name}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Firewall Rule"
        description="Define traffic rules for your VPC network"
        size="2xl"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <FormField label="Name" required help="Lowercase letters, numbers, and hyphens only">
                <Input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="allow-http"
                  pattern="[a-z]([-a-z0-9]*[a-z0-9])?"
                  required
                />
              </FormField>
            </div>

            <div className="col-span-2">
              <FormField label="Network" required>
                <Select
                  value={formData.network}
                  onChange={(e) => setFormData({ ...formData, network: e.target.value })}
                  required
                >
                  <option value="">Select a network</option>
                  {networks.map((network) => (
                    <option key={network.name} value={network.selfLink}>
                      {network.name}
                    </option>
                  ))}
                </Select>
              </FormField>
            </div>

            <FormField label="Direction" required>
              <Select
                value={formData.direction}
                onChange={(e) => setFormData({ ...formData, direction: e.target.value })}
              >
                <option value="INGRESS">Ingress (incoming)</option>
                <option value="EGRESS">Egress (outgoing)</option>
              </Select>
            </FormField>

            <FormField label="Action" required>
              <Select
                value={formData.action}
                onChange={(e) => setFormData({ ...formData, action: e.target.value as 'ALLOW' | 'DENY' })}
              >
                <option value="ALLOW">Allow</option>
                <option value="DENY">Deny</option>
              </Select>
            </FormField>

            <FormField label="Priority" required help="0-65535 (lower = higher priority)">
              <Input
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                min="0"
                max="65535"
                required
              />
            </FormField>

            <FormField label="Protocol" required>
              <Select
                value={formData.protocol}
                onChange={(e) => setFormData({ ...formData, protocol: e.target.value })}
              >
                <option value="tcp">TCP</option>
                <option value="udp">UDP</option>
                <option value="icmp">ICMP</option>
                <option value="all">All protocols</option>
              </Select>
            </FormField>

            <div className="col-span-2">
              <FormField
                label="Source IP Ranges"
                required
                help="Comma-separated CIDR ranges (e.g., 0.0.0.0/0, 10.0.0.0/8)"
              >
                <Input
                  type="text"
                  value={formData.sourceRanges}
                  onChange={(e) => setFormData({ ...formData, sourceRanges: e.target.value })}
                  placeholder="0.0.0.0/0"
                  className="font-mono"
                  required
                />
              </FormField>
            </div>

            <div className="col-span-2">
              <FormField
                label="Ports"
                help="Comma-separated ports or ranges (e.g., 80,443,8080-8090). Leave empty for all ports."
              >
                <Input
                  type="text"
                  value={formData.ports}
                  onChange={(e) => setFormData({ ...formData, ports: e.target.value })}
                  placeholder="80,443,8080-8090"
                  className="font-mono"
                />
              </FormField>
            </div>

            <div className="col-span-2">
              <FormField
                label="Target Tags"
                help="Comma-separated tags. Leave empty to apply to all instances."
              >
                <Input
                  type="text"
                  value={formData.targetTags}
                  onChange={(e) => setFormData({ ...formData, targetTags: e.target.value })}
                  placeholder="web-server,app-server"
                />
              </FormField>
            </div>
          </div>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
              disabled={createLoading}
            >
              Cancel
            </ModalButton>
            <ModalButton
              variant="primary"
              type="submit"
              loading={createLoading}
              disabled={networks.length === 0}
            >
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default FirewallsPage;
