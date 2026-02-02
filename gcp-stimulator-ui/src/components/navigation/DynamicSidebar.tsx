import { Link, useLocation, useParams } from 'react-router-dom';
import { getServiceById, ServiceLink } from '../../config/serviceCatalog';

const DynamicSidebar = () => {
  const location = useLocation();
  const params = useParams<{ serviceName: string }>();
  
  const serviceName = params.serviceName;
  const service = serviceName ? getServiceById(serviceName) : null;

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Don't show sidebar on homepage or if service has no navigation
  if (!service || !service.sidebarLinks || service.sidebarLinks.length === 0) {
    return null;
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          {service.icon && <service.icon className="w-6 h-6 text-blue-600" />}
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{service.name}</h2>
            <p className="text-xs text-gray-500 mt-0.5">{service.category}</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {service.sidebarLinks.map((link: ServiceLink) => {
            const Icon = link.icon;
            const active = isActive(link.path);

            return (
              <li key={link.path}>
                <Link
                  to={link.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    active
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {Icon && <Icon className="w-5 h-5" />}
                  <span>{link.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Server Running</span>
          </div>
          <div className="mt-1">Port: 8080</div>
        </div>
      </div>
    </aside>
  );
};

export default DynamicSidebar;
