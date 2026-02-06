import { X } from 'lucide-react';
import { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  '2xl': 'max-w-6xl',
};

export const Modal = ({ isOpen, onClose, title, description, children, size = 'md' }: ModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity animate-fadeIn"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className={`relative bg-white rounded-2xl shadow-2xl ${sizeClasses[size]} w-full transform transition-all animate-slideUp border border-gray-100`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-gray-200 flex items-start justify-between bg-gradient-to-r from-gray-50 to-white">
            <div className="flex-1 pr-4">
              <h2 className="text-[18px] font-bold text-gray-900">{title}</h2>
              {description && (
                <p className="text-[13px] text-gray-600 mt-1">{description}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-lg p-2 transition-all flex-shrink-0"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Content */}
          <div className="px-6 py-6 max-h-[calc(100vh-200px)] overflow-y-auto custom-scrollbar">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ModalFooterProps {
  children: ReactNode;
}

export const ModalFooter = ({ children }: ModalFooterProps) => (
  <div className="flex justify-end gap-3 pt-6 border-t border-gray-100 mt-6">
    {children}
  </div>
);

interface ModalButtonProps {
  onClick?: () => void;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  loading?: boolean;
  children: ReactNode;
}

export const ModalButton = ({
  onClick,
  type = 'button',
  variant = 'secondary',
  disabled = false,
  loading = false,
  children,
}: ModalButtonProps) => {
  const baseClasses = 'px-4 py-2.5 text-[13px] font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md';
  
  const variantClasses = {
    primary: 'text-white bg-blue-600 hover:bg-blue-700',
    secondary: 'text-gray-700 bg-white border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${variantClasses[variant]}`}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
          Loading...
        </span>
      ) : children}
    </button>
  );
};
