import { Link } from 'react-router-dom';
import { HardDrive, Plus, FolderOpen, Activity, ArrowRight } from 'lucide-react';
import { useBuckets } from '../hooks/useBuckets';
import { useStorageStats } from '../hooks/useStorageStats';
import { useEffect, useState } from 'react';
import { formatBytes } from '../utils/formatBytes';
import { formatDistanceToNow } from 'date-fns';
import CreateBucketModal from '../components/buckets/CreateBucketModal';
import { Modal } from '../components/Modal';

const StorageDashboardPage = () => {
  const { buckets, refresh: refreshBuckets } = useBuckets();
  const { totalObjects, totalStorageBytes, refresh: refreshStats } = useStorageStats();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [isActivityModalOpen, setActivityModalOpen] = useState(false);

  useEffect(() => {
    refreshBuckets();
    refreshStats();
  }, [refreshBuckets, refreshStats]);

  const handleBucketCreated = () => {
    setCreateModalOpen(false);
    refreshBuckets();
    refreshStats();
  };

  // Get all buckets sorted by time created
  const sortedBuckets = [...buckets]
    .sort((a, b) => new Date(b.timeCreated).getTime() - new Date(a.timeCreated).getTime());

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Hero Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-start gap-4 mb-2">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <HardDrive className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h1 className="text-[28px] font-bold text-gray-900 mb-2">Cloud Storage</h1>
                  <p className="text-[14px] text-gray-600 leading-relaxed">
                    Object storage emulator with full bucket & object lifecycle support.
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={() => setCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Bucket
            </button>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{buckets.length}</span> Buckets
              </span>
            </div>
            <button
              onClick={() => setActivityModalOpen(true)}
              className="flex items-center gap-2 hover:bg-purple-50 px-3 py-2 rounded-lg transition-colors cursor-pointer group"
            >
              <div className="w-2 h-2 bg-purple-500 rounded-full group-hover:scale-125 transition-transform"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900 group-hover:text-purple-600">{totalObjects}</span> Objects
              </span>
            </button>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{formatBytes(totalStorageBytes)}</span> Used
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* Buckets */}
        <div className="mb-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Buckets</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            {sortedBuckets.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {sortedBuckets.map((bucket) => (
                  <Link
                    key={bucket.name}
                    to={`/services/storage/buckets/${bucket.name}`}
                    className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                        <HardDrive className="w-4 h-4 text-blue-600" />
                      </div>
                      <span className="text-[14px] font-medium text-gray-900">{bucket.name}</span>
                    </div>
                    <span className="text-[12px] text-gray-500">
                      Updated {formatDistanceToNow(new Date(bucket.timeCreated), { addSuffix: true })}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <p className="text-[13px] text-gray-500">No buckets yet</p>
                <button
                  onClick={() => setCreateModalOpen(true)}
                  className="mt-3 inline-flex items-center gap-2 px-4 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Create Your First Bucket
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            <div className="divide-y divide-gray-200">
              {buckets.slice(0, 5).map((bucket, index) => (
                <div key={bucket.name} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <Activity className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-[13px] font-medium text-gray-900">
                        Bucket created: <span className="text-blue-600">{bucket.name}</span>
                      </p>
                      <p className="text-[12px] text-gray-500">
                        {bucket.location} • {bucket.storageClass}
                      </p>
                    </div>
                  </div>
                  <span className="text-[12px] text-gray-500">
                    {formatDistanceToNow(new Date(bucket.timeCreated), { addSuffix: true })}
                  </span>
                </div>
              ))}
              {buckets.length === 0 && (
                <div className="p-8 text-center">
                  <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-[13px] text-gray-500">No recent activity</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <CreateBucketModal
        isOpen={isCreateModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onBucketCreated={handleBucketCreated}
      />

      {/* Object Activity Modal */}
      <Modal
        isOpen={isActivityModalOpen}
        onClose={() => setActivityModalOpen(false)}
        title="Recent Object Activity"
      >
        <div className="space-y-2">
          {buckets.slice(0, 10).map((bucket) => (
            <div key={bucket.name} className="p-3 hover:bg-gray-50 rounded-lg transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <HardDrive className="w-4 h-4 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-[13px] font-medium text-gray-900">
                      Objects in <Link to={`/services/storage/buckets/${bucket.name}`} className="text-blue-600 hover:underline">{bucket.name}</Link>
                    </p>
                    <p className="text-[12px] text-gray-500">{bucket.location} • {bucket.storageClass}</p>
                  </div>
                </div>
                <span className="text-[12px] text-gray-500">
                  {formatDistanceToNow(new Date(bucket.timeCreated), { addSuffix: true })}
                </span>
              </div>
            </div>
          ))}
          {buckets.length === 0 && (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-[13px] text-gray-500">No object activity yet</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default StorageDashboardPage;
