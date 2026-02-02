import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, ChevronRight } from 'lucide-react';
import { serviceCategories } from '../../config/serviceCatalog';
import type { ServiceCategory, Service } from '../../config/serviceCatalog';

const ServicesMegaMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Menu className="w-5 h-5" />
        <span className="font-medium">Services</span>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-2xl border border-gray-200 z-50 w-[800px]">
          <div className="p-6 grid grid-cols-2 gap-6">
            {serviceCategories.map((category: ServiceCategory) => (
              <div key={category.id} className="space-y-3">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  {category.name}
                </h3>
                <div className="space-y-1">
                  {category.services.map((service: Service) => {
                    const Icon = service.icon;
                    const servicePath = service.enabled 
                      ? `/services/${service.id}`
                      : `/services/${service.id}`;

                    return (
                      <Link
                        key={service.id}
                        to={servicePath}
                        onClick={() => setIsOpen(false)}
                        className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                          service.enabled
                            ? 'hover:bg-blue-50 cursor-pointer'
                            : 'opacity-50 cursor-not-allowed hover:bg-gray-50'
                        }`}
                      >
                        <div className={`mt-0.5 ${service.enabled ? 'text-blue-600' : 'text-gray-400'}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium text-sm ${
                              service.enabled ? 'text-gray-900' : 'text-gray-500'
                            }`}>
                              {service.name}
                            </span>
                            {!service.enabled && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                                Coming Soon
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {service.description}
                          </p>
                        </div>
                        {service.enabled && (
                          <ChevronRight className="w-4 h-4 text-gray-400 mt-1" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ServicesMegaMenu;
