import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { ObjectEvent, Bucket } from '../types';
import { listEvents } from '../api/events';
import { fetchBuckets } from '../api/buckets';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';

const EventsPage = () => {
  const [events, setEvents] = useState<ObjectEvent[]>([]);
  const [buckets, setBuckets] = useState<string[]>([]);
  const [selectedBucket, setSelectedBucket] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadBuckets();
    loadEvents();
  }, []);

  useEffect(() => {
    loadEvents();
  }, [selectedBucket]);

  const loadBuckets = async () => {
    try {
      const bucketList = await fetchBuckets();
      setBuckets(bucketList.map((b: Bucket) => b.name));
    } catch (err) {
      console.error('Failed to load buckets:', err);
    }
  };

  const loadEvents = async () => {
    setIsLoading(true);
    try {
      const bucketFilter = selectedBucket !== 'all' ? selectedBucket : undefined;
      const eventList = await listEvents(bucketFilter);
      // Sort by timestamp descending (latest first)
      const sortedEvents = eventList.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setEvents(sortedEvents);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getEventTypeBadge = (eventType: string) => {
    const colors: Record<string, string> = {
      'OBJECT_FINALIZE': 'bg-green-100 text-green-800',
      'OBJECT_DELETE': 'bg-red-100 text-red-800',
      'OBJECT_ARCHIVE': 'bg-yellow-100 text-yellow-800',
      'OBJECT_METADATA_UPDATE': 'bg-blue-100 text-blue-800',
    };
    const colorClass = colors[eventType] || 'bg-gray-100 text-gray-800';
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
        {eventType}
      </span>
    );
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="text-indigo-600" size={32} />
            <h1 className="text-3xl font-bold text-gray-900">Object Events</h1>
          </div>
        </div>
        <p className="mt-2 text-sm text-gray-600">
          View recent object events across all buckets or filter by bucket
        </p>
      </div>

      {/* Filter Section */}
      <div className="mb-4 flex items-center gap-3">
        <label htmlFor="bucket-filter" className="text-sm font-medium text-gray-700">
          Filter by Bucket:
        </label>
        <select
          id="bucket-filter"
          value={selectedBucket}
          onChange={(e) => setSelectedBucket(e.target.value)}
          className="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="all">All Buckets</option>
          {buckets.map((bucket) => (
            <option key={bucket} value={bucket}>{bucket}</option>
          ))}
        </select>
      </div>

      {/* Events Table */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Spinner />
        </div>
      ) : events.length === 0 ? (
        <EmptyState
          title="No events found"
          description={
            selectedBucket === 'all'
              ? 'No object events have been recorded yet'
              : `No events found for bucket "${selectedBucket}"`
          }
        />
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bucket
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Object
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Generation
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Delivered
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {events.map((event) => (
                <tr key={event.event_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getEventTypeBadge(event.event_type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {event.bucket_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                    {event.object_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {event.generation}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(event.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      event.delivered ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {event.delivered ? 'Yes' : 'Pending'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* Summary Footer */}
          <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Showing <span className="font-medium">{events.length}</span> event{events.length !== 1 ? 's' : ''}
              {selectedBucket !== 'all' && (
                <span> for bucket <span className="font-mono font-medium">{selectedBucket}</span></span>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsPage;
