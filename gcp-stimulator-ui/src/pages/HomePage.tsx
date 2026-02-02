import { Link } from 'react-router-dom';
import { serviceCategories } from '../config/serviceCatalog';
import { ArrowRight, Clock, Zap, Server, Database } from 'lucide-react';

const HomePage = () => {
  // Get enabled services for quick actions
  const enabledServices = serviceCategories
    .flatMap(category => category.services)
    .filter(service => service.enabled);

  // Mock recently accessed services (in real app, this would come from localStorage/backend)
  const recentlyUsed = [
    { id: 'storage', name: 'Cloud Storage', lastAccessed: '2 minutes ago', action: 'Managed buckets' },
    { id: 'compute-engine', name: 'Compute Engine', lastAccessed: '15 minutes ago', action: 'Created VM instance' },
    { id: 'iam', name: 'IAM & Admin', lastAccessed: '1 hour ago', action: 'Viewed service accounts' },
  ];

  return (
    <div className="h-full overflow-auto bg-gray-50">
      {/* Hero Section - Stats & Quick Info */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white px-8 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm mb-2">Local Development Environment</p>
              <h1 className="text-3xl font-bold mb-2">
                Ready to build and test GCP applications locally
              </h1>
              <p className="text-blue-100">
                Full-featured emulator with gcloud CLI compatibility
              </p>
            </div>
            <div className="hidden lg:flex items-center gap-3">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg px-6 py-4 border border-white/20">
                <div className="text-3xl font-bold mb-1">{enabledServices.length}</div>
                <div className="text-sm text-blue-100">Active Services</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg px-6 py-4 border border-white/20">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <div className="text-xl font-bold">Online</div>
                </div>
                <div className="text-sm text-blue-100">localhost:8080</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Quick Actions</h2>
            <p className="text-gray-600 text-sm">Jump into your active services</p>
          </div>
          <Link 
            to="/services/storage" 
            className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            View all services <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {enabledServices.map((service) => {
            const Icon = service.icon;
            return (
              <Link
                key={service.id}
                to={`/services/${service.id}`}
                className="group bg-white rounded-xl border border-gray-200 p-6 hover:border-blue-500 hover:shadow-lg transition-all"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-lg bg-blue-50 group-hover:bg-blue-100 transition-colors">
                    <Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{service.name}</h3>
                <p className="text-sm text-gray-500 line-clamp-2">{service.description}</p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recently Used Services */}
      <div className="max-w-7xl mx-auto px-8 pb-12">
        <div className="flex items-center gap-2 mb-6">
          <Clock className="w-5 h-5 text-gray-600" />
          <h2 className="text-2xl font-bold text-gray-900">Recently Used</h2>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {recentlyUsed.map((item) => {
            const service = enabledServices.find(s => s.id === item.id);
            if (!service) return null;
            const Icon = service.icon;

            return (
              <Link
                key={item.id}
                to={`/services/${item.id}`}
                className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-gray-100 group-hover:bg-blue-50 transition-colors">
                    <Icon className="w-5 h-5 text-gray-600 group-hover:text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{item.name}</h3>
                    <p className="text-sm text-gray-500">{item.action}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">{item.lastAccessed}</span>
                  <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-600" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-gray-100 border-t border-gray-200 px-8 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-2 mb-6">
            <Zap className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-bold text-gray-900">System Status</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-5 border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <Server className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Backend Server</h3>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Running on localhost:8080</span>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-5 border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <Database className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Database</h3>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">PostgreSQL connected</span>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-5 border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <Zap className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Active Services</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-blue-600">{enabledServices.length}</span>
                <span className="text-sm text-gray-600">services ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
