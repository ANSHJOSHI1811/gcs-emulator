import { Bucket } from "../../types";
import { formatDistanceToNow } from "date-fns";
import { Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

interface BucketCardProps {
  bucket: Bucket;
  onDelete: () => void;
}

export default function BucketCard({ bucket, onDelete }: BucketCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl hover:border-blue-500 border-2 border-transparent transition-all duration-300 p-4 flex flex-col justify-between">
      <Link to={`/buckets/${bucket.name}`} className="flex-grow">
        <h3 className="text-lg font-semibold text-gray-800 truncate">{bucket.name}</h3>
        <p className="text-sm text-gray-500">{bucket.location}</p>
        <p className="text-sm text-gray-500">{bucket.storageClass}</p>
        <p className="text-xs text-gray-400 mt-2">
          Created {formatDistanceToNow(new Date(bucket.timeCreated), { addSuffix: true })}
        </p>
      </Link>
      <div className="mt-4 flex justify-end space-x-2">
        <button
          onClick={onDelete}
          className="p-2 text-gray-500 hover:text-red-600"
          title="Delete Bucket"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  );
}
