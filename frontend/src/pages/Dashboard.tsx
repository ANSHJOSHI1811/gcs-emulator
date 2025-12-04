import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useBuckets } from "../hooks/useBuckets";
import CreateBucketModal from "../components/buckets/CreateBucketModal";
import { HardDrive, File, Database } from "lucide-react";
import Spinner from "../components/common/Spinner";
import EmptyState from "../components/common/EmptyState";

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
  const { buckets, loadBuckets, isLoading, error } = useBuckets();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);

  useEffect(() => {
    loadBuckets();
  }, [loadBuckets]);

  const handleBucketCreated = () => {
    setCreateModalOpen(false);
    loadBuckets();
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h1>
      
      {isLoading && <Spinner />}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error}</span></div>}
      
      {!isLoading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard title="Buckets" value={buckets.length} icon={HardDrive} loading={isLoading} />
            <StatCard title="Objects (TODO)" value="0" icon={File} loading={false} />
            <StatCard title="Storage (TODO)" value="0 GB" icon={Database} loading={false} />
          </div>

          {buckets.length === 0 && (
            <div className="mt-8">
              <EmptyState 
                title="No buckets yet"
                description="Get started by creating your first bucket."
                actionButton={
                  <button
                    onClick={() => setCreateModalOpen(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                  >
                    Create Bucket
                  </button>
                }
              />
            </div>
          )}

          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Quick Actions</h2>
            <div className="flex space-x-4">
              <button
                onClick={() => navigate("/buckets")}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
              >
                View Buckets
              </button>
              <button
                onClick={() => setCreateModalOpen(true)}
                className="bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition"
              >
                Create New Bucket
              </button>
            </div>
          </div>
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

