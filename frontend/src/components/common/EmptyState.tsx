import { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  actionButton?: ReactNode;
}

export default function EmptyState({ title, description, actionButton }: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-4">
      <h3 className="mt-2 text-lg font-medium text-gray-900">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {actionButton && <div className="mt-6">{actionButton}</div>}
    </div>
  );
}
