import { AlertCircle } from 'lucide-react';
import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface FormFieldProps {
  label: string;
  required?: boolean;
  help?: string;
  error?: string;
  children: React.ReactNode;
}

export const FormField = ({ label, required, help, error, children }: FormFieldProps) => (
  <div>
    <label className="block text-sm font-semibold text-gray-700 mb-2">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    {children}
    {help && !error && (
      <p className="mt-2 text-xs text-gray-500 flex items-center gap-1">
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
        {help}
      </p>
    )}
    {error && (
      <p className="mt-2 text-xs text-red-600 flex items-center gap-1">
        <AlertCircle className="w-3.5 h-3.5" />
        {error}
      </p>
    )}
  </div>
);

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  fullWidth?: boolean;
}

export const Input = ({ fullWidth = true, className = '', ...props }: InputProps) => (
  <input
    className={`${fullWidth ? 'w-full' : ''} px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all ${className}`}
    {...props}
  />
);

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  fullWidth?: boolean;
}

export const Textarea = ({ fullWidth = true, className = '', ...props }: TextareaProps) => (
  <textarea
    className={`${fullWidth ? 'w-full' : ''} px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none ${className}`}
    {...props}
  />
);

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  fullWidth?: boolean;
}

export const Select = ({ fullWidth = true, className = '', children, ...props }: SelectProps) => (
  <select
    className={`${fullWidth ? 'w-full' : ''} px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white ${className}`}
    {...props}
  >
    {children}
  </select>
);

interface RadioGroupProps {
  options: Array<{ value: string; label: string; description?: string }>;
  value: string | boolean;
  onChange: (value: any) => void;
  name: string;
}

export const RadioGroup = ({ options, value, onChange, name }: RadioGroupProps) => (
  <div className="space-y-3">
    {options.map((option) => {
      const isSelected = option.value === value.toString();
      return (
        <label
          key={option.value}
          className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all hover:shadow-sm ${
            isSelected
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <input
            type="radio"
            name={name}
            checked={isSelected}
            onChange={() => onChange(option.value === 'true' ? true : option.value === 'false' ? false : option.value)}
            className="mt-1 text-blue-600 focus:ring-blue-500"
          />
          <div>
            <div className="text-sm font-semibold text-gray-900">{option.label}</div>
            {option.description && (
              <div className="text-xs text-gray-600 mt-0.5">{option.description}</div>
            )}
          </div>
        </label>
      );
    })}
  </div>
);
