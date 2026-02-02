import { Bucket } from "../../types";
import { formatDistanceToNow } from "date-fns";
import { Trash2, HardDrive, MapPin, Clock } from "lucide-react";
import { Link } from "react-router-dom";

interface BucketCardProps {
  bucket: Bucket;
  onDelete: () => void;
}

export default function BucketCard({ bucket, onDelete }: BucketCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const confirmed = window.confirm(
      `Delete bucket "${bucket.name}"?\n\n` +
      `⚠️ Warning: This will permanently delete the bucket and ALL objects inside it.\n\n` +
      `Make sure all objects are deleted first, or the deletion will fail.`
    );
    
    if (confirmed) {
      onDelete();
    }
  };

  const getStorageClassColor = (storageClass: string) => {
    switch (storageClass) {
      case 'STANDARD':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'NEARLINE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'COLDLINE':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'ARCHIVE':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <Link 
      to={`/services/storage/buckets/${bucket.name}`}
      className="block bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] border border-gray-200/60 hover:border-blue-400/60 transition-all duration-200 overflow-hidden group relative"
    >
      <div className="p-4">
        {/* Top Row: Icon + Name + Created Date */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-center justify-center w-9 h-9 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors flex-shrink-0">
            <HardDrive className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="text-[15px] font-bold text-gray-900 truncate flex-1 group-hover:text-blue-600 transition-colors">
            {bucket.name}
          </h3>
          <div className="flex items-center gap-1.5 text-[11px] text-gray-500 flex-shrink-0">
            <Clock className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">
              {formatDistanceToNow(new Date(bucket.timeCreated), { addSuffix: true })}
            </span>
          </div>
        </div>

        {/* Bottom Row: Storage Class + Location */}
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center text-[11px] font-semibold px-2.5 py-1 rounded-full border shadow-sm ${getStorageClassColor(bucket.storageClass)}`}>
            {bucket.storageClass}
          </span>
          <div className="flex items-center gap-1.5 text-[12px] text-gray-600">
            <MapPin className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
            <span className="truncate">{bucket.location}</span>
          </div>
        </div>

        {/* Delete Button - Bottom Right */}
        <button
          onClick={handleDelete}
          className="absolute bottom-3 right-3 flex items-center justify-center w-8 h-8 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
          title="Delete bucket"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </Link>
  );
}
