interface DropdownFilterProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { label: string; value: string }[];
}

export default function DropdownFilter({ label, value, onChange, options }: DropdownFilterProps) {
  return (
    <div>
      <label htmlFor={label} className="block text-sm font-medium text-gray-700">{label}</label>
      <select
        id={label}
        name={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </div>
  );
}
