import { Link } from 'react-router-dom';
import { HardDrive, Plus, FolderOpen, Activity, ArrowRight } from 'lucide-react';
import { useBuckets } from '../hooks/useBuckets';
import { useStorageStats } from '../hooks/useStorageStats';
import { useEffect, useState } from 'react';
import { formatBytes } from '../utils/formatBytes';
import { formatDistanceToNow } from 'date-fns';
import CreateBucketModal from '../components/buckets/CreateBucketModal';

const StorageDashboardPage = () => {
  const { buckets, refresh: refreshBuckets } = useBuckets();
  const { totalObjects, totalStorageBytes, refresh: refreshStats } = useStorageStats();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);

  useEffect(() => {
    refreshBuckets();
    refreshStats();
  }, [refreshBuckets, refreshStats]);

  const handleBucketCreated = () => {
    setCreateModalOpen(false);
    refreshBuckets();
    refreshStats();
  };

  // Get recent buckets (top 3, sorted by time created)
  const recentBuckets = [...buckets]
    .sort((a, b) => new Date(b.timeCreated).getTime() - new Date(a.timeCreated).getTime())
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Hero Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-8 py-8">
          <div className="flex items-start gap-4 mb-6">
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

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Bucket
            </button>
            <Link
              to="/services/storage/buckets"
              className="inline-flex items-center gap-2 px-4 h-10 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all text-[13px] font-medium"
            >
              <FolderOpen className="w-4 h-4" />
              Browse Buckets
            </Link>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{buckets.length}</span> Buckets
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{totalObjects}</span> Objects
              </span>
            </div>
            <div className="flex items-center gap-2">
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
        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/services/storage/buckets"
              className="bg-white rounded-lg border border-gray-200 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] hover:border-blue-400/60 transition-all group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                  <FolderOpen className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-[14px] font-semibold text-gray-900">Browse</h3>
              </div>
              <p className="text-[12px] text-gray-600">View and manage all buckets</p>
            </Link>

            <button
              onClick={() => setCreateModalOpen(true)}
              className="bg-white rounded-lg border border-gray-200 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] hover:border-green-400/60 transition-all group text-left"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-green-50 rounded-lg group-hover:bg-green-100 transition-colors">
                  <Plus className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="text-[14px] font-semibold text-gray-900">Create</h3>
              </div>
              <p className="text-[12px] text-gray-600">Set up a new bucket</p>
            </button>

            <Link
              to="/services/storage/activity"
              className="bg-white rounded-lg border border-gray-200 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] hover:border-purple-400/60 transition-all group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-purple-50 rounded-lg group-hover:bg-purple-100 transition-colors">
                  <Activity className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-[14px] font-semibold text-gray-900">View Logs</h3>
              </div>
              <p className="text-[12px] text-gray-600">Monitor activity and events</p>
            </Link>
          </div>
        </div>

        {/* Recent Buckets */}
        <div>
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Buckets</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            {recentBuckets.length > 0 ? (
              <>
                <div className="divide-y divide-gray-200">
                  {recentBuckets.map((bucket) => (
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
                <div className="border-t border-gray-200">
                  <Link
                    to="/services/storage/buckets"
                    className="flex items-center justify-center gap-2 p-3 text-[13px] font-medium text-blue-600 hover:bg-blue-50 transition-colors"
                  >
                    View All
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </>
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
      </div>

      <CreateBucketModal
        isOpen={isCreateModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onBucketCreated={handleBucketCreated}
      />
    </div>
  );
};

export default StorageDashboardPage;
