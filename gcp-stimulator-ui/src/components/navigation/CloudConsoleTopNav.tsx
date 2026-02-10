import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home, Cloud, Search } from 'lucide-react';
import ServicesMegaMenu from '../navigation/ServicesMegaMenu';
import ProjectSelector from '../ProjectSelector';
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
    <header className="h-16 bg-white border-b border-gray-200">
      <div className="h-full max-w-full mx-auto px-6 flex items-center justify-between gap-6">
        {/* Left Section */}
        <div className="flex items-center gap-6 flex-1 min-w-0">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 flex-shrink-0 group">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-400 rounded-lg blur opacity-25 group-hover:opacity-40 transition-opacity"></div>
              <div className="relative w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                <Cloud className="w-5 h-5 text-white" strokeWidth={2} />
              </div>
            </div>
            <div className="hidden lg:flex flex-col">
              <span className="text-[15px] font-semibold text-gray-900 leading-none">Cloud Stimulator</span>
              <span className="text-[11px] text-gray-500 leading-none mt-0.5">Development Environment</span>
            </div>
          </Link>

          {/* Services Menu */}
          <ServicesMegaMenu />

          {/* Breadcrumbs */}
          <nav className="flex items-center gap-1 min-w-0 overflow-x-auto no-scrollbar md:hidden">
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.path} className="flex items-center gap-1 flex-shrink-0">
                {index > 0 && (
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
                <Link
                  to={crumb.path}
                  className={`text-sm px-2 py-1 rounded hover:bg-gray-100 transition-colors ${
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

        {/* Right Section */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {/* Project Selector */}
          <ProjectSelector />
        </div>
      </div>
    </header>
  );
};

export default CloudConsoleTopNav;
