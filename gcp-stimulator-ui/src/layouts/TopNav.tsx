import { useLocation, Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

const TopNav = () => {
  const location = useLocation();

  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean);
    
    if (paths.length === 0) {
      return [{ label: 'Dashboard', path: '/' }];
    }

    const breadcrumbs = [{ label: 'Dashboard', path: '/' }];

    if (paths[0] === 'buckets') {
      breadcrumbs.push({ label: 'Buckets', path: '/buckets' });
      
      if (paths[1]) {
        breadcrumbs.push({ 
          label: decodeURIComponent(paths[1]), 
          path: `/buckets/${paths[1]}` 
        });
        
        if (paths[2] === 'objects' && paths[3]) {
          breadcrumbs.push({ 
            label: decodeURIComponent(paths[3]), 
            path: `/buckets/${paths[1]}/objects/${paths[3]}` 
          });
        }
      }
    }

    if (paths[0] === 'settings') {
      breadcrumbs.push({ label: 'Settings', path: '/settings' });
    }

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center">
      <nav className="flex items-center gap-2">
        {breadcrumbs.map((crumb, index) => (
          <div key={crumb.path} className="flex items-center gap-2">
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )}
            {index === breadcrumbs.length - 1 ? (
              <span className="text-gray-900 font-medium">{crumb.label}</span>
            ) : (
              <Link
                to={crumb.path}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </div>
        ))}
      </nav>
    </header>
  );
};

export default TopNav;
