import { useEffect, useState, useMemo } from "react";
import { ComputeInstance } from "@/types/compute";
import { fetchInstances, deleteInstance, startInstance, stopInstance, ZONES } from "@/api/compute";
import CreateInstanceModal from "../components/compute/CreateInstanceModal";
import DeleteConfirmModal from "@/components/common/DeleteConfirmModal";
import Spinner from "@/components/common/Spinner";
import { Plus, Server, Search, Play, Square } from "lucide-react";
import { useNavigate } from "react-router-dom";

const STATUS_COLORS: Record<string, string> = {
  RUNNING: "bg-green-100 text-green-800 border-green-200",
  STOPPED: "bg-gray-100 text-gray-800 border-gray-200",
  TERMINATED: "bg-gray-100 text-gray-800 border-gray-200",
  PROVISIONING: "bg-blue-100 text-blue-800 border-blue-200",
  STAGING: "bg-blue-100 text-blue-800 border-blue-200",
  STOPPING: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

export default function InstanceListPage() {
  const navigate = useNavigate();
  const [instances, setInstances] = useState<ComputeInstance[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<ComputeInstance | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedZone, setSelectedZone] = useState(ZONES[0].value);

  const loadInstances = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchInstances(selectedZone);
      setInstances(data);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to load instances");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInstances();
  }, [selectedZone]);

  const handleDelete = async () => {
    if (!selectedInstance) return;
    try {
      await deleteInstance(selectedInstance.zone, selectedInstance.name);
      setDeleteModalOpen(false);
      setSelectedInstance(null);
      loadInstances();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to delete instance");
    }
  };

  const handleStart = async (instance: ComputeInstance) => {
    try {
      await startInstance(instance.zone, instance.name);
      loadInstances();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to start instance");
    }
  };

  const handleStop = async (instance: ComputeInstance) => {
    try {
      await stopInstance(instance.zone, instance.name);
      loadInstances();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to stop instance");
    }
  };

  const openDeleteModal = (instance: ComputeInstance) => {
    setSelectedInstance(instance);
    setDeleteModalOpen(true);
  };

  const handleInstanceCreated = () => {
    setCreateModalOpen(false);
    loadInstances();
  };

  const filteredInstances = useMemo(() => {
    return instances.filter((instance) =>
      instance.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [instances, searchTerm]);

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-24 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <Spinner />
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg px-5 py-4 flex items-start gap-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)]" role="alert">
          <div className="flex-shrink-0 w-5 h-5 mt-0.5">
            <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="text-[13px] font-medium text-red-800">{error}</span>
        </div>
      );
    }

    if (instances.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Server className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-[15px] font-semibold text-gray-900 mb-2">No instances found</h3>
          <p className="text-[13px] text-gray-500 mb-6">Create your first VM instance to get started with Compute Engine.</p>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-all font-medium shadow-sm hover:shadow-md text-[13px]"
          >
            <Plus className="w-4 h-4" />
            Create Your First Instance
          </button>
        </div>
      );
    }

    if (filteredInstances.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mb-3">
            <Server className="w-7 h-7 text-gray-400" />
          </div>
          <h3 className="text-[15px] font-semibold text-gray-900 mb-1">No instances match your search</h3>
          <p className="text-[13px] text-gray-500">Try adjusting your search criteria.</p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Name</th>
                <th className="text-left px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Zone</th>
                <th className="text-left px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Machine Type</th>
                <th className="text-left px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                <th className="text-left px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Created</th>
                <th className="text-right px-6 py-3 text-[12px] font-semibold text-gray-700 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredInstances.map((instance) => (
                <tr
                  key={instance.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/services/compute/instances/${instance.name}?zone=${instance.zone}`)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Server className="w-4 h-4 text-gray-400" />
                      <span className="text-[13px] font-medium text-blue-600 hover:underline">{instance.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[13px] text-gray-700">{instance.zone}</td>
                  <td className="px-6 py-4 text-[13px] text-gray-700 font-mono">{instance.machineType}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${STATUS_COLORS[instance.status] || STATUS_COLORS.TERMINATED}`}>
                      {instance.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-[13px] text-gray-600">
                    {new Date(instance.creationTimestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-2">
                      {instance.status === "RUNNING" ? (
                        <button
                          onClick={() => handleStop(instance)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-md hover:bg-yellow-100 transition-colors"
                          title="Stop instance"
                        >
                          <Square className="w-3.5 h-3.5" />
                          Stop
                        </button>
                      ) : instance.status === "TERMINATED" ? (
                        <button
                          onClick={() => handleStart(instance)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100 transition-colors"
                          title="Start instance"
                        >
                          <Play className="w-3.5 h-3.5" />
                          Start
                        </button>
                      ) : null}
                      <button
                        onClick={() => openDeleteModal(instance)}
                        className="px-3 py-1.5 text-[12px] font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="max-w-[1280px] mx-auto px-8 py-4">
          <div className="flex items-center gap-4">
            {/* Title + Count */}
            <div className="flex items-baseline gap-3 min-w-[200px]">
              <h1 className="text-[20px] font-bold text-gray-900">VM Instances</h1>
              <span className="text-[13px] text-gray-500 font-medium">
                {instances.length} total
              </span>
            </div>

            {/* Zone Selector */}
            <div className="flex-none">
              <select
                value={selectedZone}
                onChange={(e) => setSelectedZone(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-[13px] bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              >
                {ZONES.map((zone) => (
                  <option key={zone.value} value={zone.value}>
                    {zone.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Search */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search instances..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-[13px] bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                />
              </div>
            </div>

            {/* Create Button */}
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex-none inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition-all font-medium shadow-sm hover:shadow-md text-[13px]"
            >
              <Plus className="w-4 h-4" />
              Create Instance
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-6">
        {renderContent()}
      </div>

      {/* Modals */}
      <CreateInstanceModal
        isOpen={isCreateModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={handleInstanceCreated}
        zone={selectedZone}
      />

      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setSelectedInstance(null);
        }}
        onConfirm={handleDelete}
        title="Delete VM Instance"
        description={
          selectedInstance
            ? `Are you sure you want to delete "${selectedInstance.name}"? This action cannot be undone.`
            : ""
        }
      />
    </div>
  );
}
