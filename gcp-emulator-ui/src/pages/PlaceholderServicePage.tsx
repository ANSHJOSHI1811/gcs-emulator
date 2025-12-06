import { useParams, Navigate } from 'react-router-dom';
import { AlertCircle, Construction } from 'lucide-react';
import { getServiceById } from '../config/serviceCatalog';

const PlaceholderServicePage = () => {
  const { serviceName } = useParams<{ serviceName: string }>();
  const service = serviceName ? getServiceById(serviceName) : null;

  // If service is enabled (like storage), redirect to its default view
  if (service?.enabled) {
    return <Navigate to={`/services/${serviceName}/buckets`} replace />;
  }

  if (!service) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Service Not Found
          </h2>
          <p className="text-gray-600">
            The service you're looking for doesn't exist in the catalog.
          </p>
        </div>
      </div>
    );
  }

  const Icon = service.icon;

  return (
    <div className="h-full flex items-center justify-center p-6">
      <div className="text-center max-w-2xl">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6">
          <Icon className="w-10 h-10 text-blue-600" />
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {service.name}
        </h1>
        
        <p className="text-lg text-gray-600 mb-8">
          {service.description}
        </p>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <Construction className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
            <div className="text-left">
              <h3 className="font-semibold text-yellow-900 mb-2">
                Coming Soon
              </h3>
              <p className="text-sm text-yellow-800">
                This service is not yet implemented in the GCS Emulator. 
                Currently, only <strong>Cloud Storage</strong> is fully functional. 
                Stay tuned for future updates!
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 text-sm text-gray-500">
          <p>Category: <span className="font-medium text-gray-700">{service.category}</span></p>
        </div>
      </div>
    </div>
  );
};

export default PlaceholderServicePage;
