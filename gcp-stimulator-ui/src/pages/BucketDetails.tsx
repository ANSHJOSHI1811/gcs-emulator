import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useObjects } from '../hooks/useObjects';
import { downloadObject } from '../api/objects';
import { format } from 'date-fns';
import { Download, Trash2, Upload, Settings, Lock, Unlock, FileText, Clock, HardDrive } from 'lucide-react';
import UploadObjectModal from '../components/UploadObjectModal';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import SearchInput from '../components/common/SearchInput';
import DropdownFilter from '../components/common/DropdownFilter';
import Pagination from '../components/common/Pagination';
import SecurityBanner from '../components/common/SecurityBanner';
import BucketSettingsModal from '../components/BucketSettingsModal';
import { Modal } from '../components/Modal';
import { ACLValue } from '../types';
import { getBucketACL } from '../api/buckets';
import toast from 'react-hot-toast';

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
  const [isSettingsModalOpen, setSettingsModalOpen] = useState(false);
  const [isObjectDetailsOpen, setObjectDetailsOpen] = useState(false);
  const [selectedObject, setSelectedObject] = useState<any>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [contentTypeFilter, setContentTypeFilter] = useState("");
  const [sizeRangeFilter, setSizeRangeFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  
  // Phase 4: Bucket ACL state
  const [bucketACL, setBucketACL] = useState<ACLValue>('private');
  const [isLoadingACL, setIsLoadingACL] = useState(false);

  // Phase 4: Load bucket ACL
  useEffect(() => {
    const loadBucketACL = async () => {
      if (!bucketName) return;
      setIsLoadingACL(true);
      try {
        const acl = await getBucketACL(bucketName);
        setBucketACL(acl);
      } catch (err) {
        console.error('Failed to load bucket ACL:', err);
      } finally {
        setIsLoadingACL(false);
      }
    };
    loadBucketACL();
  }, [bucketName]);

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
    if (isLoading) return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
    
    if (error) return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg flex items-center gap-3">
        <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
        <span className="font-medium">{error as string}</span>
      </div>
    );
    
    if (objects.length === 0) return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-12">
        <EmptyState 
          title="This bucket is empty" 
          description="Upload your first file to get started with Cloud Storage." 
          actionButton={
            <button 
              onClick={() => setUploadModalOpen(true)} 
              className="inline-flex items-center gap-2 px-6 py-3 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              <Upload size={18} />
              Upload File
            </button>
          } 
        />
      </div>
    );
    
    if (filteredObjects.length === 0) return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <EmptyState title="No objects match your filters" description="Try adjusting your search or filter criteria." />
      </div>
    );

    return (
      <>
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Name</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Size</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Last Modified</th>
                  <th scope="col" className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {paginatedObjects.map((obj, index) => (
                  <tr key={`${obj.name}-${obj.generation}-${index}`} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      <button 
                        onClick={() => {
                          setSelectedObject(obj);
                          setObjectDetailsOpen(true);
                        }}
                        className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2"
                      >
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="truncate max-w-md">{obj.name}</span>
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                      {(obj.size / 1024).toFixed(2)} KB
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {format(new Date(obj.updated), 'MMM d, yyyy, h:mm a')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleDownload(obj.name)} 
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Download"
                        >
                          <Download size={18} />
                        </button>
                        <button 
                          onClick={() => handleDelete(obj.name, obj.generation)} 
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        {filteredObjects.length > PAGE_SIZE && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalItems={filteredObjects.length}
              pageSize={PAGE_SIZE}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <SecurityBanner />
      
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1280px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Link 
                  to="/services/storage"
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                  <HardDrive className="w-5 h-5" />
                </Link>
                <span className="text-gray-400">/</span>
                <h1 className="text-2xl font-bold text-gray-900">
                  {bucketName}
                </h1>
              </div>
              {/* Bucket ACL Badge */}
              <div className="flex items-center space-x-3">
                {isLoadingACL ? (
                  <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                ) : (
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                    bucketACL === 'private' 
                      ? 'bg-gray-100 text-gray-700 border border-gray-200' 
                      : 'bg-orange-100 text-orange-700 border border-orange-200'
                  }`}>
                    {bucketACL === 'private' ? (
                      <Lock size={12} />
                    ) : (
                      <Unlock size={12} />
                    )}
                    {bucketACL}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSettingsModalOpen(true)}
                className="inline-flex items-center gap-2 px-4 h-10 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all text-[13px] font-medium"
              >
                <Settings size={16} />
                Settings
              </button>
              <button
                onClick={() => setUploadModalOpen(true)}
                className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
              >
                <Upload size={16} />
                Upload Object
              </button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{objects.length}</span> {objects.length === 1 ? 'Object' : 'Objects'}
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{(objects.reduce((acc, obj) => acc + obj.size, 0) / 1024).toFixed(2)}</span> KB Total
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                Storage Class: <span className="font-semibold text-gray-900">STANDARD</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* Filters Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SearchInput
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search by object name..."
            />
            <DropdownFilter
              label="Content Type"
              value={contentTypeFilter}
              onChange={setContentTypeFilter}
              options={contentTypeOptions}
            />
            <DropdownFilter
              label="Size Range"
              value={sizeRangeFilter}
              onChange={setSizeRangeFilter}
              options={SIZE_RANGE_OPTIONS}
            />
          </div>
        </div>

        {/* Objects List */}
        {renderContent()}
      </div>

      {bucketName && (
        <>
          <UploadObjectModal
            isOpen={isUploadModalOpen}
            onClose={() => setUploadModalOpen(false)}
            bucketName={bucketName}
            onUploaded={handleUploadSuccess}
          />
          <BucketSettingsModal
            isOpen={isSettingsModalOpen}
            onClose={() => setSettingsModalOpen(false)}
            bucketName={bucketName}
            currentACL={bucketACL}
            onACLUpdate={(newACL) => {
              setBucketACL(newACL);
              toast.success(`✅ Bucket ACL updated to ${newACL}`);
            }}
          />
          {selectedObject && (
            <Modal
              isOpen={isObjectDetailsOpen}
              onClose={() => {
                setObjectDetailsOpen(false);
                setSelectedObject(null);
              }}
              title="Object Details"
            >
              <div className="space-y-6">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-blue-500 mt-1" />
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-500">Object Name</h3>
                    <p className="mt-1 text-lg font-semibold text-gray-900 break-all">{selectedObject.name}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Size</h3>
                    <p className="mt-1 text-base text-gray-900 font-mono">{(selectedObject.size / 1024).toFixed(2)} KB</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Content Type</h3>
                    <p className="mt-1 text-base text-gray-900">{selectedObject.contentType || 'application/octet-stream'}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-gray-400 mt-1" />
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-500">Created / Updated</h3>
                    <p className="mt-1 text-base text-gray-900">{format(new Date(selectedObject.updated), 'MMM d, yyyy, h:mm a')}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Storage Details</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2 font-mono text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Bucket:</span>
                      <span className="text-gray-900">{bucketName}</span>
                    </div>
                    {selectedObject.generation && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Generation:</span>
                        <span className="text-gray-900">{selectedObject.generation}</span>
                      </div>
                    )}
                    {selectedObject.md5Hash && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">MD5:</span>
                        <span className="text-gray-900 break-all">{selectedObject.md5Hash}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex gap-3 pt-4 border-t">
                  <button
                    onClick={() => {
                      handleDownload(selectedObject.name);
                      setObjectDetailsOpen(false);
                      setSelectedObject(null);
                    }}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download size={18} />
                    Download
                  </button>
                  <button
                    onClick={() => {
                      handleDelete(selectedObject.name, selectedObject.generation);
                      setObjectDetailsOpen(false);
                      setSelectedObject(null);
                    }}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Trash2 size={18} />
                    Delete
                  </button>
                </div>
              </div>
            </Modal>
          )}
        </>
      )}
    </div>
  );
};

export default BucketDetails;
