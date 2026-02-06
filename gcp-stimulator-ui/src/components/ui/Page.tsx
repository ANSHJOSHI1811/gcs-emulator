import { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  breadcrumbs?: ReactNode;
}

export const PageHeader = ({ title, subtitle, icon, actions, breadcrumbs }: PageHeaderProps) => (
  <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
    <div className="max-w-7xl mx-auto px-6 py-4">
      {breadcrumbs && <div className="mb-3">{breadcrumbs}</div>}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {icon && (
            <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg">
              {icon}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-900 truncate">{title}</h1>
            {subtitle && <p className="text-sm text-gray-600 mt-0.5 truncate">{subtitle}</p>}
          </div>
        </div>
        {actions && <div className="flex-shrink-0 ml-4">{actions}</div>}
      </div>
    </div>
  </div>
);

interface PageContainerProps {
  children: ReactNode;
  maxWidth?: 'md' | 'lg' | 'xl' | '2xl' | 'full';
}

export const PageContainer = ({ children, maxWidth = 'xl' }: PageContainerProps) => {
  const maxWidthClasses = {
    md: 'max-w-4xl',
    lg: 'max-w-5xl',
    xl: 'max-w-6xl',
    '2xl': 'max-w-7xl',
    full: 'max-w-full',
  };
  
  return (
    <div className={`${maxWidthClasses[maxWidth]} mx-auto px-6 py-6`}>
      {children}
    </div>
  );
};
