import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'blue' | 'purple';
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge = ({ children, variant = 'default', size = 'md', dot = false }: BadgeProps) => {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };
  
  const variantClasses = {
    default: 'bg-gray-100 text-gray-700 border-gray-200',
    success: 'bg-green-50 text-green-700 border-green-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    error: 'bg-red-50 text-red-700 border-red-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    blue: 'bg-blue-100 text-blue-700 border-blue-300',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  };
  
  const dotColors = {
    default: 'bg-gray-500',
    success: 'bg-green-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  };
  
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${sizeClasses[size]} ${variantClasses[variant]}`}>
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
