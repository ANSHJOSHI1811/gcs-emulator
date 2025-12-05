import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useObjects } from '../hooks/useObjects';
import { downloadObject } from '../api/objects';
import { format } from 'date-fns';
import { Download, Trash2, Upload } from 'lucide-react';
import UploadObjectModal from '../components/UploadObjectModal';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import SearchInput from '../components/common/SearchInput';
import DropdownFilter from '../components/common/DropdownFilter';
import Pagination from '../components/common/Pagination';

const PAGE_SIZE = 20;

const SIZE_RANGE_OPTIONS = [
  { label: "All", value: "" },
  { label: "0-1 MB", value: "0-1048576" },
  { label: "1-10 MB", value: "1048576-10485760" },
  { label: "10MB+", value: "10485760-" },
];

const BucketDetails = () => {
  const { bucketName } = useParams<{ bucketName: string }>();
  const { objects, isLoading, error, refresh, handleDelete } = useObjects(bucketName!);
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [contentTypeFilter, setContentTypeFilter] = useState("");
  const [sizeRangeFilter, setSizeRangeFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (bucketName) {
      refresh();
    }
  }, [bucketName, refresh]);

  const contentTypeOptions = useMemo(() => {
    const types = new Set(objects.map(o => o.contentType).filter(Boolean));
    const options = Array.from(types).map(t => ({ label: t, value: t }));
    return [{ label: "All", value: "" }, ...options];
  }, [objects]);

  const filteredObjects = useMemo(() => {
    return objects
      .filter(obj => obj.name.toLowerCase().includes(searchTerm.toLowerCase()))
      .filter(obj => contentTypeFilter ? obj.contentType === contentTypeFilter : true)
      .filter(obj => {
        if (!sizeRangeFilter) return true;
        const [min, max] = sizeRangeFilter.split('-').map(Number);
        if (max) return obj.size >= min && obj.size < max;
        return obj.size >= min;
      });
  }, [objects, searchTerm, contentTypeFilter, sizeRangeFilter]);

  const paginatedObjects = useMemo(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    return filteredObjects.slice(startIndex, startIndex + PAGE_SIZE);
  }, [filteredObjects, currentPage]);

  const handleDownload = async (objectName: string) => {
    if (!bucketName) return;
    try {
      const blob = await downloadObject(bucketName, objectName);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = objectName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed", error);
    }
  };

  const handleUploadSuccess = () => {
    refresh();
    setUploadModalOpen(false);
  };

  const renderContent = () => {
    if (isLoading) return <Spinner />;
    if (error) return <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error as string}</span></div>;
    if (objects.length === 0) return <EmptyState title="This bucket is empty" description="Upload a file to get started." actionButton={<button onClick={() => setUploadModalOpen(true)} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"><Upload size={16} className="mr-2" />Upload File</button>} />;
    if (filteredObjects.length === 0) return <EmptyState title="No objects match your filters" description="Try different filter criteria." />;

    return (
      <>
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Modified</th>
                <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedObjects.map((obj, index) => (
                <tr key={`${obj.name}-${obj.generation}-${index}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <Link to={`/buckets/${bucketName}/objects/${encodeURIComponent(obj.name)}`} className="text-blue-600 hover:underline">
                      {obj.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{(obj.size / 1024).toFixed(2)} KB</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{format(new Date(obj.updated), 'MMM d, yyyy, h:mm a')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => handleDownload(obj.name)} className="text-blue-600 hover:text-blue-900 mr-4"><Download size={18} /></button>
                    <button onClick={() => handleDelete(obj.name, obj.generation)} className="text-red-600 hover:text-red-900"><Trash2 size={18} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination
          currentPage={currentPage}
          totalItems={filteredObjects.length}
          pageSize={PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      </>
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Bucket: <span className="font-mono">{bucketName}</span>
        </h1>
        <button
          onClick={() => setUploadModalOpen(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Upload size={16} className="mr-2" />
          Upload
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="md:col-span-1">
          <SearchInput
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Search by object name..."
          />
        </div>
        <div className="md:col-span-1">
          <DropdownFilter
            label="Content Type"
            value={contentTypeFilter}
            onChange={setContentTypeFilter}
            options={contentTypeOptions}
          />
        </div>
        <div className="md:col-span-1">
          <DropdownFilter
            label="Size Range"
            value={sizeRangeFilter}
            onChange={setSizeRangeFilter}
            options={SIZE_RANGE_OPTIONS}
          />
        </div>
      </div>

      {renderContent()}

      {bucketName && (
        <UploadObjectModal
          isOpen={isUploadModalOpen}
          onClose={() => setUploadModalOpen(false)}
          bucketName={bucketName}
          onUploaded={handleUploadSuccess}
        />
      )}
    </div>
  );
};

export default BucketDetails;
