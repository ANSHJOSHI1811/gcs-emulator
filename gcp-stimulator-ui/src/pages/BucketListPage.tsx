import { useEffect, useState, useMemo } from "react";
import { useBuckets } from "../hooks/useBuckets";
import BucketCard from "../components/buckets/BucketCard";
import CreateBucketModal from "../components/buckets/CreateBucketModal";
import DeleteConfirmModal from "../components/common/DeleteConfirmModal";
import { Bucket } from "../types";
import Spinner from "../components/common/Spinner";
import Pagination from "../components/common/Pagination";
import { Plus, FolderOpen, Search } from "lucide-react";

const PAGE_SIZE = 16;

const STORAGE_CLASS_OPTIONS = [
  { label: "All", value: "" },
  { label: "STANDARD", value: "STANDARD" },
  { label: "NEARLINE", value: "NEARLINE" },
  { label: "COLDLINE", value: "COLDLINE" },
  { label: "ARCHIVE", value: "ARCHIVE" },
];

export default function BucketListPage() {
  const { buckets, refresh: loadBuckets, isLoading, error, handleDeleteBucket } = useBuckets();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedBucket, setSelectedBucket] = useState<Bucket | null>(null);
  
  const [searchTerm, setSearchTerm] = useState("");
  const [storageClassFilter, setStorageClassFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadBuckets();
  }, [loadBuckets]);

  const filteredBuckets = useMemo(() => {
    return buckets
      .filter((bucket) =>
        bucket.name.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .filter((bucket) =>
        storageClassFilter ? bucket.storageClass === storageClassFilter : true
      );
  }, [buckets, searchTerm, storageClassFilter]);

  const paginatedBuckets = useMemo(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    return filteredBuckets.slice(startIndex, startIndex + PAGE_SIZE);
  }, [filteredBuckets, currentPage]);

  const openDeleteModal = (bucket: Bucket) => {
    setSelectedBucket(bucket);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    if (selectedBucket) {
      handleDeleteBucket(selectedBucket.name);
    }
  };

  const handleBucketCreated = () => {
    setCreateModalOpen(false);
    loadBuckets();
  };

  const renderContent = () => {
    if (isLoading) return (
      <div className="flex items-center justify-center py-24 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <Spinner />
      </div>
    );
    
    if (error) return (
      <div className="bg-red-50 border border-red-200 rounded-lg px-5 py-4 flex items-start gap-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)]" role="alert">
        <div className="flex-shrink-0 w-5 h-5 mt-0.5">
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="text-[13px] font-medium text-red-800">{error}</span>
      </div>
    );
    
    if (buckets.length === 0) return (
      <div className="flex flex-col items-center justify-center py-20 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <FolderOpen className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-[15px] font-semibold text-gray-900 mb-2">No buckets found</h3>
        <p className="text-[13px] text-gray-500 mb-6">Create your first bucket to get started with Cloud Storage.</p>
        <button 
          onClick={() => setCreateModalOpen(true)} 
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-all font-medium shadow-sm hover:shadow-md text-[13px]"
        >
          <Plus className="w-4 h-4" />
          Create Your First Bucket
        </button>
      </div>
    );
    
    if (filteredBuckets.length === 0) return (
      <div className="flex flex-col items-center justify-center py-16 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mb-3">
          <FolderOpen className="w-7 h-7 text-gray-400" />
        </div>
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">No buckets match your filters</h3>
        <p className="text-[13px] text-gray-500">Try adjusting your search or filter criteria.</p>
      </div>
    );

    return (
      <>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {paginatedBuckets.map((bucket) => (
            <BucketCard
              key={bucket.name}
              bucket={bucket}
              onDelete={() => openDeleteModal(bucket)}
            />
          ))}
        </div>
        {filteredBuckets.length > PAGE_SIZE && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalItems={filteredBuckets.length}
              pageSize={PAGE_SIZE}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Unified Header - Title, Count, Search, Filter */}
      <div className="bg-white border-b border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="max-w-[1280px] mx-auto px-8 py-4">
          <div className="flex items-center gap-4">
            {/* Title + Count */}
            <div className="flex items-baseline gap-3 min-w-[200px]">
              <h1 className="text-[20px] font-bold text-gray-900">Buckets</h1>
              <span className="text-[13px] text-gray-500 font-medium">
                {buckets.length} total
              </span>
            </div>

            {/* Search */}
            <div className="relative w-[280px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search buckets..."
                className="w-full h-9 pl-9 pr-3 text-[13px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
              />
            </div>

            {/* Storage Class Filter */}
            <select
              value={storageClassFilter}
              onChange={(e) => setStorageClassFilter(e.target.value)}
              className="h-9 px-3 text-[13px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white min-w-[140px]"
            >
              {STORAGE_CLASS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Results Count */}
            {(searchTerm || storageClassFilter) && (
              <div className="text-[13px] text-gray-500 font-medium">
                {filteredBuckets.length} {filteredBuckets.length === 1 ? 'result' : 'results'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-[1280px] mx-auto px-8 py-6">
        {renderContent()}
      </div>

      {/* Floating Action Button - Bottom Right */}
      <button
        onClick={() => setCreateModalOpen(true)}
        className="fixed bottom-8 right-8 z-50 flex items-center gap-2 px-5 h-12 bg-blue-600 text-white rounded-full shadow-[0_4px_16px_rgba(37,99,235,0.4)] hover:shadow-[0_6px_24px_rgba(37,99,235,0.5)] hover:bg-blue-700 transition-all duration-200 active:scale-95 group"
        title="Create new bucket"
      >
        <Plus className="w-5 h-5" />
        <span className="text-[14px] font-medium">Create Bucket</span>
      </button>

      <CreateBucketModal
        isOpen={isCreateModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onBucketCreated={handleBucketCreated}
      />
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Bucket"
        description={`Are you sure you want to delete the bucket "${selectedBucket?.name}"? This action cannot be undone.`}
      />
    </div>
  );
}
