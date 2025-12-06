import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import ServicesMegaMenu from '../navigation/ServicesMegaMenu';
import { getServiceById } from '../../config/serviceCatalog';

interface Breadcrumb {
  label: string;
  path: string;
  icon?: React.ComponentType<{ className?: string }>;
}

const CloudConsoleTopNav = () => {
  const location = useLocation();

  const getBreadcrumbs = (): Breadcrumb[] => {
    const paths = location.pathname.split('/').filter(Boolean);
    
    const breadcrumbs: Breadcrumb[] = [{ label: 'Home', path: '/', icon: Home }];

    // Handle /services/{serviceName} routes
    if (paths[0] === 'services' && paths[1]) {
      const service = getServiceById(paths[1]);
      if (service) {
        breadcrumbs.push({ 
          label: service.name, 
          path: `/services/${paths[1]}`,
        });

        // Storage-specific breadcrumbs
        if (paths[1] === 'storage') {
          if (paths[2] === 'buckets') {
            breadcrumbs.push({ label: 'Buckets', path: `/services/storage/buckets` });
            
            if (paths[3]) {
              breadcrumbs.push({ 
                label: decodeURIComponent(paths[3]), 
                path: `/services/storage/buckets/${paths[3]}` 
              });
              
              if (paths[4] === 'objects' && paths[5]) {
                breadcrumbs.push({ 
                  label: decodeURIComponent(paths[5]), 
                  path: `/services/storage/buckets/${paths[3]}/objects/${paths[5]}` 
                });
              }
            }
          } else if (paths[2] === 'settings') {
            breadcrumbs.push({ label: 'Settings', path: `/services/storage/settings` });
          }
        }
      }
    }

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 mr-2">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
            <span className="text-white font-bold text-sm">GCS</span>
          </div>
          <span className="font-semibold text-gray-900 hidden sm:inline">
            Emulator Console
          </span>
        </Link>

        <ServicesMegaMenu />

        <nav className="flex items-center gap-2 ml-4">
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.path} className="flex items-center gap-2">
              {index > 0 && (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
              <Link
                to={crumb.path}
                className={`text-sm hover:text-blue-600 transition-colors ${
                  index === breadcrumbs.length - 1
                    ? 'text-gray-900 font-medium'
                    : 'text-gray-600'
                }`}
              >
                {crumb.icon && index === 0 && crumb.icon ? (
                  <crumb.icon className="w-4 h-4" />
                ) : (
                  crumb.label
                )}
              </Link>
            </div>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-xs text-gray-500">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span className="hidden sm:inline">Connected</span>
          </span>
        </div>
      </div>
    </header>
  );
};

export default CloudConsoleTopNav;
