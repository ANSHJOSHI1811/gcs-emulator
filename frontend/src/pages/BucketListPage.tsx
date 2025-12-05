import { useEffect, useState, useMemo } from "react";
import { useBuckets } from "../hooks/useBuckets";
import BucketCard from "../components/buckets/BucketCard";
import CreateBucketModal from "../components/buckets/CreateBucketModal";
import DeleteConfirmModal from "../components/common/DeleteConfirmModal";
import { Bucket } from "../types";
import Spinner from "../components/common/Spinner";
import EmptyState from "../components/common/EmptyState";
import SearchInput from "../components/common/SearchInput";
import DropdownFilter from "../components/common/DropdownFilter";
import Pagination from "../components/common/Pagination";

const PAGE_SIZE = 10;

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
    if (isLoading) return <Spinner />;
    if (error) return <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error}</span></div>;
    if (buckets.length === 0) return <EmptyState title="No buckets found" description="Create a new bucket to get started." actionButton={<button onClick={() => setCreateModalOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition">Create Bucket</button>} />;
    if (filteredBuckets.length === 0) return <EmptyState title="No buckets match your filters" description="Try different filter criteria." />;

    return (
      <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {paginatedBuckets.map((bucket) => (
            <BucketCard
              key={bucket.name}
              bucket={bucket}
              onDelete={() => openDeleteModal(bucket)}
            />
          ))}
        </div>
        <Pagination
          currentPage={currentPage}
          totalItems={filteredBuckets.length}
          pageSize={PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      </>
    );
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Buckets</h1>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          Create Bucket
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search by bucket name..."
        />
        <DropdownFilter
          label="Storage Class"
          value={storageClassFilter}
          onChange={setStorageClassFilter}
          options={STORAGE_CLASS_OPTIONS}
        />
      </div>

      {renderContent()}

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
