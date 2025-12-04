import { useState, useEffect } from 'react';
import { useHealth } from '../hooks/useHealth';
import Spinner from '../components/common/Spinner';
import { RefreshCw } from 'lucide-react';

const SettingsPage = () => {
  const { healthStatus, storageStats, isLoading, error, refresh } = useHealth();

  // Local UI Preferences
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [pageSize, setPageSize] = useState(() => localStorage.getItem('defaultPageSize') || '20');

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('defaultPageSize', pageSize);
  }, [pageSize]);

  const renderHealthStatus = () => {
    if (!healthStatus) return null;

    const statusIndicator = {
      healthy: { color: 'bg-green-500', text: 'Healthy' },
      unhealthy: { color: 'bg-red-500', text: 'Unhealthy' },
      unknown: { color: 'bg-yellow-500', text: 'Unknown' },
    };

    const { color, text } = statusIndicator[healthStatus.status];

    return (
      <div className="flex items-center">
        <span className={`w-3 h-3 rounded-full mr-2 ${color}`}></span>
        <span>{text}</span>
        {healthStatus.message && <span className="text-gray-500 ml-2 text-sm">({healthStatus.message})</span>}
      </div>
    );
  };

  const StatCard = ({ label, value }: { label: string; value: string | number | undefined }) => (
    <div className="bg-gray-50 p-4 rounded-lg">
      <dt className="text-sm font-medium text-gray-500 truncate">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold text-gray-900">{value ?? 'N/A'}</dd>
    </div>
  );

  return (
    <div className="p-6 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isLoading && <Spinner />}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">{error}</div>}

      {!isLoading && !error && (
        <div className="space-y-6">
          {/* API Status Section */}
          <div className="p-4 bg-white shadow rounded-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">API Connection Status</h2>
            {renderHealthStatus()}
          </div>

          {/* Storage Stats Section */}
          <div className="p-4 bg-white shadow rounded-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Storage Stats</h2>
            <dl className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <StatCard label="Total Buckets" value={storageStats?.totalBuckets} />
              <StatCard label="Total Objects" value={storageStats?.totalObjects} />
              <StatCard label="Estimated Storage Used" value={storageStats?.approximateStorageUsed === 'N/A' ? 'N/A' : `${(storageStats?.approximateStorageUsed as number / 1024 / 1024).toFixed(2)} MB`} />
            </dl>
          </div>

          {/* UI Preferences Section */}
          <div className="p-4 bg-white shadow rounded-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">UI Preferences</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="theme-select" className="text-sm font-medium text-gray-700">Theme</label>
                <select
                  id="theme-select"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="mt-1 block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </div>
              <div className="flex items-center justify-between">
                <label htmlFor="pagesize-select" className="text-sm font-medium text-gray-700">Default Page Size</label>
                <select
                  id="pagesize-select"
                  value={pageSize}
                  onChange={(e) => setPageSize(e.target.value)}
                  className="mt-1 block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                >
                  <option value="5">5</option>
                  <option value="10">10</option>
                  <option value="20">20</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
