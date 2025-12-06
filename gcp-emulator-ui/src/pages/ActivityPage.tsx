import { Activity, Construction } from 'lucide-react';

const ActivityPage = () => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Activity</h1>
        <p className="text-sm text-gray-600 mt-1">
          Monitor storage operations and events
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
              <Construction className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-yellow-900 mb-2">
              Activity Dashboard Coming Soon
            </h3>
            <p className="text-sm text-yellow-800 mb-4">
              This page will display real-time activity logs, storage operations, 
              and event tracking for your Cloud Storage resources.
            </p>
            <div className="bg-white border border-yellow-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Planned Features:</h4>
              <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                <li>Real-time operation logs</li>
                <li>Storage access patterns</li>
                <li>API request monitoring</li>
                <li>Error tracking and alerts</li>
                <li>Performance metrics</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Recent Operations</h3>
          </div>
          <p className="text-sm text-gray-500">View and filter recent storage operations</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-gray-900">Event Logs</h3>
          </div>
          <p className="text-sm text-gray-500">Track bucket and object lifecycle events</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Access Analytics</h3>
          </div>
          <p className="text-sm text-gray-500">Analyze access patterns and usage trends</p>
        </div>
      </div>
    </div>
  );
};

export default ActivityPage;
