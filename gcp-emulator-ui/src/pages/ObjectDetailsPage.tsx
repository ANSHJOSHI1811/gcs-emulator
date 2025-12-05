import { useParams, useNavigate } from 'react-router-dom';
import { useObjectDetails } from '../hooks/useObjectDetails';
import { format } from 'date-fns';
import { ArrowLeft, Download, Trash2 } from 'lucide-react';
import { downloadObject } from '../api/objects';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';

const ObjectDetailsPage = () => {
  const { bucketName, objectName } = useParams<{ bucketName: string; objectName: string }>();
  const navigate = useNavigate();
  const { metadata, versions, isLoading, error, deleteVersion } = useObjectDetails(bucketName, objectName);

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
                <dt className="text-sm font-medium text-gray-500">Size</dt>
                <dd className="mt-1 text-sm text-gray-900">{(metadata.size / 1024).toFixed(2)} KB</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Last Modified</dt>
                <dd className="mt-1 text-sm text-gray-900">{format(new Date(metadata.updated), 'MMM d, yyyy, h:mm a')}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Generation</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{metadata.generation}</dd>
              </div>
              {/* TODO: Add other metadata fields like contentType and metageneration when available from backend */}
            </dl>
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
