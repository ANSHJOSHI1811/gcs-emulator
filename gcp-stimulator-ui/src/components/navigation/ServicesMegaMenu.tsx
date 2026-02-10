import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, ChevronRight, Search, X } from 'lucide-react';
import { serviceCategories } from '../../config/serviceCatalog';
import type { ServiceCategory, Service } from '../../config/serviceCatalog';

const ServicesMegaMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      // Focus search input when menu opens
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Filter services based on search query
  const filteredCategories = serviceCategories.map(category => ({
    ...category,
    services: category.services.filter(service => 
      service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.services.length > 0);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
          isOpen ? 'bg-blue-50 text-blue-700 shadow-sm' : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        <Menu className="w-4 h-4" />
        <span>Services</span>
      </button>

      {isOpen && (
        <>
          <div className="absolute top-full left-0 mt-3 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/80 z-50 w-[900px] overflow-hidden">
            <div className="bg-gradient-to-br from-blue-50/50 to-transparent p-1">
              <div className="bg-white/90 backdrop-blur-sm rounded-xl">
                {/* Search Bar */}
                <div className="p-4 border-b border-gray-200/80">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search services, products, and docs..."
                      className="w-full pl-10 pr-10 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                    />
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Services Grid */}
                <div className="p-8 grid grid-cols-2 gap-8 max-h-[600px] overflow-y-auto">
                  {filteredCategories.length > 0 ? (
                    filteredCategories.map((category: ServiceCategory) => (
                    <div key={category.id} className="space-y-4">
                      <div className="flex items-center gap-2">
                        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                        <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.1em] px-2">
                          {category.name}
                        </h3>
                        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                      </div>
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
                              onClick={() => {
                                setIsOpen(false);
                                setSearchQuery('');
                              }}
                              className={`group flex items-start gap-3 p-3 rounded-xl border transition-all duration-200 ${
                                service.enabled
                                  ? 'hover:bg-blue-50/80 hover:border-blue-200/60 hover:shadow-md hover:-translate-y-0.5 cursor-pointer border-transparent'
                                  : 'opacity-60 cursor-not-allowed hover:bg-gray-50/50 border-transparent'
                              }`}
                            >
                              <div className={`mt-0.5 p-2 rounded-lg transition-all duration-200 flex-shrink-0 ${
                                service.enabled 
                                  ? 'text-blue-600 bg-blue-50 group-hover:bg-blue-100 group-hover:scale-110' 
                                  : 'text-gray-400 bg-gray-100'
                              }`}>
                                <Icon className="w-4 h-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`font-semibold text-[13px] ${
                                    service.enabled ? 'text-gray-900' : 'text-gray-500'
                                  }`}>
                                    {service.name}
                                  </span>
                                  {!service.enabled && (
                                    <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
                                      Coming Soon
                                    </span>
                                  )}
                                </div>
                                <p className="text-[11px] text-gray-500 leading-relaxed line-clamp-1">
                                  {service.description}
                                </p>
                              </div>
                              {service.enabled && (
                                <ChevronRight className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    </div>
                  ))
                  ) : (
                    <div className="col-span-2 text-center py-12">
                      <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-500">No services found matching "{searchQuery}"</p>
                      <button
                        onClick={() => setSearchQuery('')}
                        className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Clear search
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/5 backdrop-blur-[2px] -z-10" onClick={() => setIsOpen(false)}></div>
        </>
      )}
    </div>
  );
};

export default ServicesMegaMenu;
