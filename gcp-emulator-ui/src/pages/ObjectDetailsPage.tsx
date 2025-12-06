import { useParams, useNavigate } from 'react-router-dom';
import { useObjectDetails } from '../hooks/useObjectDetails';
import { format } from 'date-fns';
import { ArrowLeft, Download, Trash2, Link as LinkIcon, Check, Lock, Unlock } from 'lucide-react';
import { downloadObject } from '../api/objects';
import { generateSignedUrl } from '../api/signedUrlApi';
import { getObjectACL, updateObjectACL } from '../api/objects';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { ACLValue } from '../types';

const ObjectDetailsPage = () => {
  const { bucketName, objectName } = useParams<{ bucketName: string; objectName: string }>();
  const navigate = useNavigate();
  const { metadata, versions, isLoading, error, deleteVersion } = useObjectDetails(bucketName, objectName);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [isGeneratingUrl, setIsGeneratingUrl] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Phase 4: ACL state
  const [objectACL, setObjectACL] = useState<ACLValue>('private');
  const [isLoadingACL, setIsLoadingACL] = useState(false);
  const [isUpdatingACL, setIsUpdatingACL] = useState(false);

  // Phase 4: Load object ACL
  useEffect(() => {
    const loadACL = async () => {
      if (!bucketName || !objectName) return;
      setIsLoadingACL(true);
      try {
        const acl = await getObjectACL(bucketName, objectName);
        setObjectACL(acl);
      } catch (err) {
        console.error('Failed to load object ACL:', err);
      } finally {
        setIsLoadingACL(false);
      }
    };
    loadACL();
  }, [bucketName, objectName]);

  // Phase 4: Update object ACL
  const handleUpdateACL = async (newACL: ACLValue) => {
    if (!bucketName || !objectName) return;
    setIsUpdatingACL(true);
    try {
      await updateObjectACL(bucketName, objectName, newACL);
      setObjectACL(newACL);
      toast.success(`✅ Object ACL updated to ${newACL}`);
    } catch (err) {
      console.error('Failed to update object ACL:', err);
      toast.error('❌ Failed to update object ACL');
    } finally {
      setIsUpdatingACL(false);
    }
  };

  const handleDownload = async (generation?: string) => {
    if (!bucketName || !objectName) return;
    try {
      const blob = await downloadObject(bucketName, objectName, generation);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = objectName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed", err);
    }
  };

  const handleDelete = async (generation: string) => {
    if (window.confirm(`Are you sure you want to delete version ${generation}?`)) {
      try {
        await deleteVersion(generation);
      } catch (err) {
        console.error("Delete failed", err);
        alert("Failed to delete version.");
      }
    }
  };

  const handleGenerateSignedUrl = async () => {
    if (!bucketName || !objectName) return;
    setIsGeneratingUrl(true);
    try {
      const url = await generateSignedUrl(bucketName, objectName, "GET", 3600);
      setSignedUrl(url);
      toast.success("✅ Signed URL generated (valid for 1 hour)");
    } catch (err) {
      console.error("Failed to generate signed URL", err);
      toast.error("❌ Failed to generate signed URL");
    } finally {
      setIsGeneratingUrl(false);
    }
  };

  const handleCopySignedUrl = () => {
    if (signedUrl) {
      navigator.clipboard.writeText(signedUrl);
      setCopied(true);
      toast.success("✅ Signed URL copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return <Spinner />;
    }

    if (error) {
      return <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error}</span></div>;
    }

    if (!metadata) {
      return <EmptyState title="Object not found" description="The requested object does not exist." />;
    }

    return (
      <div className="space-y-6">
        {/* Metadata Section */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Object: <span className="font-mono">{metadata.name}</span>
          </h1>
          <div className="mt-4 p-4 bg-white shadow rounded-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Metadata</h2>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Bucket</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{metadata.bucket}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Size</dt>
                <dd className="mt-1 text-sm text-gray-900">{(metadata.size / 1024).toFixed(2)} KB</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Content Type</dt>
                <dd className="mt-1 text-sm text-gray-900">{metadata.contentType || 'application/octet-stream'}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Last Modified</dt>
                <dd className="mt-1 text-sm text-gray-900">{format(new Date(metadata.updated), 'MMM d, yyyy, h:mm a')}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Generation</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{metadata.generation}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Metageneration</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{metadata.metageneration}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">MD5 Hash</dt>
                <dd className="mt-1 text-xs text-gray-900 font-mono break-all">{metadata.md5Hash || 'N/A'}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">CRC32C</dt>
                <dd className="mt-1 text-xs text-gray-900 font-mono break-all">{metadata.crc32c || 'N/A'}</dd>
              </div>
              {/* Phase 4: Storage Class Indicator */}
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Storage Class</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {metadata.storageClass === 'ARCHIVE' ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      ARCHIVE
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {metadata.storageClass || 'STANDARD'}
                    </span>
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Phase 4: Object ACL Management */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Access Control (Phase 4)</h2>
          <div className="p-4 bg-white shadow rounded-lg">
            <p className="text-sm text-gray-600 mb-3">
              Control who can access this object. "private" requires authentication, "publicRead" allows anonymous access.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <label htmlFor="object-acl" className="block text-sm font-medium text-gray-700 mb-1">
                  Current ACL
                </label>
                <select
                  id="object-acl"
                  value={objectACL}
                  onChange={(e) => handleUpdateACL(e.target.value as ACLValue)}
                  disabled={isLoadingACL || isUpdatingACL}
                  className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="private">Private (Authenticated access only)</option>
                  <option value="publicRead">Public Read (Anonymous access allowed)</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                {isLoadingACL || isUpdatingACL ? (
                  <div className="animate-spin h-5 w-5 border-2 border-indigo-600 border-t-transparent rounded-full"></div>
                ) : objectACL === 'private' ? (
                  <Lock size={20} className="text-gray-600" />
                ) : (
                  <Unlock size={20} className="text-orange-600" />
                )}
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  objectACL === 'private' ? 'bg-gray-100 text-gray-800' : 'bg-orange-100 text-orange-800'
                }`}>
                  {objectACL}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Phase 3: Signed URL Section */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Signed URL (Phase 3)</h2>
          <div className="p-4 bg-white shadow rounded-lg">
            <p className="text-sm text-gray-600 mb-3">
              Generate a temporary signed URL for secure download without authentication.
            </p>
            <button
              onClick={handleGenerateSignedUrl}
              disabled={isGeneratingUrl}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <LinkIcon size={16} className="mr-2" />
              {isGeneratingUrl ? "Generating..." : "Generate Signed URL"}
            </button>
            
            {signedUrl && (
              <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
                <div className="flex justify-between items-start">
                  <div className="flex-1 mr-2">
                    <p className="text-xs font-medium text-gray-700 mb-1">Signed URL (expires in 1 hour):</p>
                    <p className="text-xs text-gray-600 font-mono break-all">{signedUrl}</p>
                  </div>
                  <button
                    onClick={handleCopySignedUrl}
                    className="flex-shrink-0 inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {copied ? (
                      <>
                        <Check size={14} className="mr-1 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <LinkIcon size={14} className="mr-1" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Version History Section */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Version History</h2>
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Generation</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                  <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {versions.map((v) => (
                  <tr key={v.generation} className={v.isLatest ? 'bg-green-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {v.generation} {v.isLatest && <span className="ml-2 text-xs font-semibold text-green-800">(Latest)</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{format(new Date(v.updated), 'MMM d, yyyy, h:mm a')}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{(v.size ? v.size / 1024 : 0).toFixed(2)} KB</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button onClick={() => handleDownload(v.generation)} className="text-blue-600 hover:text-blue-900 mr-4"><Download size={18} /></button>
                      {!v.isLatest && (
                         <button onClick={() => handleDelete(v.generation)} className="text-red-600 hover:text-red-900"><Trash2 size={18} /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {versions.length === 0 && !isLoading && (
              <EmptyState title="No version history found" description="This object does not have any other versions." />
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <button
        onClick={() => navigate(`/buckets/${bucketName}`)}
        className="inline-flex items-center mb-4 px-3 py-1 border border-transparent text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200"
      >
        <ArrowLeft size={16} className="mr-2" />
        Back to Bucket
      </button>
      {renderContent()}
    </div>
  );
};

export default ObjectDetailsPage;
