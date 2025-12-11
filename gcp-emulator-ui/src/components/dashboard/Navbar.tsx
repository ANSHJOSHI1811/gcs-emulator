import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/' },
    { label: 'Storage', path: '/services/storage' },
    { label: 'Compute', path: '/services/compute' },
    { label: 'IAM', path: '/services/iam' },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="w-full h-16 bg-white/95 backdrop-blur border-b border-gray-200 shadow-sm flex items-center px-10">
      {/* Left side - Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center text-white font-bold text-base tracking-tight">
          GCS
        </div>
        <span className="text-lg font-semibold text-gray-800">Simulator Console</span>
      </div>

      {/* Center - Navigation Tabs */}
      <div className="flex-1 flex items-center justify-center gap-6">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              isActive(item.path)
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {/* Right side - Status & User */}
      <div className="flex items-center gap-4 text-sm text-gray-700">
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-green-50 border border-green-100">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="font-medium text-green-700">Connected</span>
        </div>
        <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center border border-gray-300 shadow-inner">
          <svg
            className="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
