import { Link } from 'react-router-dom';

interface ServiceCardProps {
  name: string;
  icon?: string;
  status: 'Active' | 'Coming Soon';
  path?: string;
}

const ServiceCard = ({ name, icon, status, path }: ServiceCardProps) => {
  const isActive = status === 'Active';

  const content = (
    <div
      className={`
        bg-white rounded-2xl border border-gray-200 shadow-md 
        p-6 flex flex-col items-center gap-3
        transition-all duration-200 ease-out
        ${
          isActive
            ? 'hover:shadow-lg hover:-translate-y-1 cursor-pointer'
            : 'opacity-80'
        }
      `}
    >
      {/* Icon placeholder */}
      <div className="w-12 h-12 bg-blue-50 border border-blue-100 rounded-xl flex items-center justify-center">
        <span className="text-xl text-blue-600 font-semibold">
          {icon || name.charAt(0)}
        </span>
      </div>

      {/* Service name */}
      <div className="text-base font-semibold text-gray-900 text-center leading-tight">{name}</div>

      {/* Status pill */}
      <div
        className={`
          px-3 py-1 rounded-full text-xs font-semibold tracking-wide inline-flex items-center gap-1
          ${
            isActive
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600'
          }
        `}
      >
        {status}
      </div>
    </div>
  );

  if (isActive && path) {
    return <Link to={path}>{content}</Link>;
  }

  return content;
};

export default ServiceCard;
