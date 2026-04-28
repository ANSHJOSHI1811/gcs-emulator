import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export const Card = ({ children, className = '', hover = false, onClick }: CardProps) => {
  const hoverClass = hover ? 'hover:shadow-lg hover:scale-[1.01] cursor-pointer' : '';
  const clickable = onClick ? 'cursor-pointer' : '';
  
  return (
    <div 
      className={`bg-white rounded-xl border border-gray-200 shadow-sm transition-all duration-200 ${hoverClass} ${clickable} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export const CardHeader = ({ title, subtitle, action, icon }: CardHeaderProps) => (
  <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
    <div className="flex items-center gap-3 flex-1">
      {icon && <div className="text-blue-600">{icon}</div>}
      <div className="flex-1 min-w-0">
        <h3 className="text-base font-semibold text-gray-900 truncate">{title}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5 truncate">{subtitle}</p>}
      </div>
    </div>
    {action && <div className="flex-shrink-0 ml-4">{action}</div>}
  </div>
);

interface CardBodyProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const CardBody = ({ children, className = '', padding = 'md' }: CardBodyProps) => {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-6',
  };
  
  return (
    <div className={`${paddingClasses[padding]} ${className}`}>
      {children}
    </div>
  );
};

interface CardFooterProps {
  children: ReactNode;
  className?: string;
}

export const CardFooter = ({ children, className = '' }: CardFooterProps) => (
  <div className={`px-5 py-3 border-t border-gray-100 bg-gray-50 rounded-b-xl ${className}`}>
    {children}
  </div>
);
