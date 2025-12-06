import { Shield } from 'lucide-react';

export default function SecurityBanner() {
  return (
    <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
      <div className="flex">
        <div className="flex-shrink-0">
          <Shield className="h-5 w-5 text-blue-400" />
        </div>
        <div className="ml-3">
          <p className="text-sm text-blue-700">
            <strong>Security Update:</strong> Object names are now validated to prevent path traversal attacks. 
            Names cannot contain "..", backslashes, or absolute paths.
          </p>
        </div>
      </div>
    </div>
  );
}
