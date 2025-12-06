import { Link } from 'react-router-dom';
import { serviceCategories } from '../config/serviceCatalog';
import { ArrowRight } from 'lucide-react';

const HomePage = () => {
  return (
    <div className="h-full overflow-auto">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-12">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-3">
            Welcome to GCS Emulator Console
          </h1>
          <p className="text-xl text-blue-100 mb-6">
            Local development environment for Google Cloud Platform services
          </p>
          <Link
            to="/services/storage"
            className="inline-flex items-center gap-2 bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            Explore Cloud Storage
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Services Grid */}
      <div className="max-w-7xl mx-auto px-8 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Available Services
        </h2>
        <p className="text-gray-600 mb-8">
          Explore our cloud services catalog
        </p>

        <div className="space-y-10">
          {serviceCategories.map((category) => (
            <div key={category.id}>
              <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <span className="w-1 h-6 bg-blue-600 rounded"></span>
                {category.name}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {category.services.map((service) => {
                  const Icon = service.icon;
                  const servicePath = `/services/${service.id}`;

                  return (
                    <Link
                      key={service.id}
                      to={servicePath}
                      className={`block bg-white rounded-lg border-2 transition-all ${
                        service.enabled
                          ? 'border-gray-200 hover:border-blue-500 hover:shadow-md cursor-pointer'
                          : 'border-gray-100 opacity-60 cursor-not-allowed'
                      }`}
                    >
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div className={`p-3 rounded-lg ${
                            service.enabled ? 'bg-blue-50' : 'bg-gray-50'
                          }`}>
                            <Icon className={`w-6 h-6 ${
                              service.enabled ? 'text-blue-600' : 'text-gray-400'
                            }`} />
                          </div>
                          {!service.enabled && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              Coming Soon
                            </span>
                          )}
                          {service.enabled && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-medium">
                              Active
                            </span>
                          )}
                        </div>
                        
                        <h4 className="font-semibold text-gray-900 mb-2">
                          {service.name}
                        </h4>
                        
                        <p className="text-sm text-gray-600">
                          {service.description}
                        </p>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-gray-100 border-t border-gray-200 px-8 py-8 mt-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg p-6">
              <div className="text-3xl font-bold text-blue-600 mb-2">1</div>
              <div className="text-sm text-gray-600">Active Service</div>
              <div className="text-xs text-gray-500 mt-1">Cloud Storage</div>
            </div>
            
            <div className="bg-white rounded-lg p-6">
              <div className="text-3xl font-bold text-gray-400 mb-2">5</div>
              <div className="text-sm text-gray-600">Coming Soon</div>
              <div className="text-xs text-gray-500 mt-1">More services in development</div>
            </div>
            
            <div className="bg-white rounded-lg p-6">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div className="text-lg font-semibold text-gray-900">Online</div>
              </div>
              <div className="text-sm text-gray-600">Server Status</div>
              <div className="text-xs text-gray-500 mt-1">localhost:8080</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
