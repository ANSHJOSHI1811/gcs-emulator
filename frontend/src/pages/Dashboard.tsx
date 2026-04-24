import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useBuckets } from "../hooks/useBuckets";
import { useStorageStats } from "../hooks/useStorageStats";
import CreateBucketModal from "../components/buckets/CreateBucketModal";
import { HardDrive, File, Database } from "lucide-react";
import Spinner from "../components/common/Spinner";
import EmptyState from "../components/common/EmptyState";
import { formatBytes } from "../utils/formatBytes";

const StatCard = ({ title, value, icon: Icon, loading }: { title: string, value: string | number, icon: React.ElementType, loading: boolean }) => (
  <div className="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
    <div className="bg-blue-100 p-3 rounded-full">
      <Icon className="text-blue-600" size={24} />
    </div>
    <div>
      <p className="text-sm text-gray-500">{title}</p>
      {loading ? <div className="h-6 w-12 bg-gray-200 rounded animate-pulse"></div> : <p className="text-2xl font-semibold text-gray-800">{value}</p>}
    </div>
  </div>
);

export default function Dashboard() {
  const navigate = useNavigate();
  const { buckets, isLoading: bucketsLoading, error: bucketsError, refresh: refreshBuckets } = useBuckets();
  const { totalObjects, totalStorageBytes, isLoading: statsLoading, error: statsError, refresh: refreshStats } = useStorageStats();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);

  useEffect(() => {
    refreshBuckets();
    refreshStats();
  }, []);

  const isLoading = bucketsLoading || statsLoading;
  const error = bucketsError || statsError;

  const handleBucketCreated = () => {
    setCreateModalOpen(false);
    refreshBuckets();
    refreshStats();
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h1>
      
      {isLoading && <Spinner />}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error as string}</span></div>}
      
      {!isLoading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard title="Buckets" value={buckets.length} icon={HardDrive} loading={bucketsLoading} />
            <StatCard title="Total Objects" value={totalObjects} icon={File} loading={statsLoading} />
            <StatCard title="Total Storage" value={formatBytes(totalStorageBytes)} icon={Database} loading={statsLoading} />
          </div>

          {buckets.length === 0 ? (
            <div className="mt-8">
              <EmptyState 
                title="No buckets found"
                description="Get started by creating a new bucket."
                actionButton={
                  <button
                    onClick={() => setCreateModalOpen(true)}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Create Bucket
                  </button>
                }
              />
            </div>
          ) : (
            <div className="mt-8 bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Recent Buckets</h2>
                <button
                  onClick={() => navigate('/services/storage/buckets')}
                  className="text-sm font-medium text-blue-600 hover:text-blue-800"
                >
                  View All
                </button>
              </div>
              <ul className="divide-y divide-gray-200">
                {buckets.slice(0, 5).map((bucket) => (
                  <li key={bucket.name} className="py-3 flex items-center justify-between">
                    <span className="font-mono text-gray-700">{bucket.name}</span>
                    <span className="text-sm text-gray-500">{bucket.location}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      
      <CreateBucketModal
        isOpen={isCreateModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onBucketCreated={handleBucketCreated}
      />
    </div>
  );
}

