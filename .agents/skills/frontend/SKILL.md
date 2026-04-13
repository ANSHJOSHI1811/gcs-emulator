## Skill: Unified Frontend UI Expert

**name:** Frontend Development  
**description:** Expert in React 18 + TypeScript + Tailwind CSS + Vite for the GCP Stimulator UI. Builds pages, components, forms, and API integrations following existing project conventions. Auto-activates for any UI/component/page work.

**trigger_keywords:** React, component, UI, Vite, Tailwind, TypeScript, page, useState, useContext, Form, modal, dashboard, table, button, sidebar, navigate, redirect, responsive, hook

**allowed_tools:** Read, Grep, Semantic Search, File Search

---

## Project Structure

```
gcp-stimulator-ui/src/
├── pages/               ← Full-page views (one per GCP service)
├── components/          ← Reusable UI components (Modal, FormFields, etc.)
├── api/                 ← Axios API clients (one file per service)
├── contexts/            ← React Context providers (ProjectContext, etc.)
├── hooks/               ← Custom React hooks
├── layouts/             ← Layout wrappers (sidebar + header shells)
├── types/               ← TypeScript interfaces shared across pages
├── utils/               ← Helper functions
├── config/              ← Config values (API base URL, project ID)
├── App.tsx              ← React Router routes definition
└── main.tsx             ← Entry point
```

---

## Core Patterns

### Page Component Pattern
**All pages follow this exact structure — copy this when adding a new page:**

```tsx
import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { apiClient } from '../api/client';
import { SomeIcon, Plus, Trash2, RefreshCw } from 'lucide-react';

// 1. Define interfaces at the top
interface MyResource {
  id: string;
  name: string;
  status: string;
  createdAt: string;
}

const MyServicePage = () => {
  // 2. Always get project from context
  const { currentProject } = useProject();

  // 3. Standard state setup
  const [resources, setResources] = useState<MyResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 4. Fetch on mount + project change
  useEffect(() => {
    fetchResources();
  }, [currentProject]);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const resp = await apiClient.get(
        `/compute/v1/projects/${currentProject}/zones/us-central1-a/myresources`
      );
      setResources(resp.data.items || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load resources');
    } finally {
      setLoading(false);
    }
  };

  // 5. Loading/error/empty states handled before main content
  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" /></div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <SomeIcon className="h-6 w-6 text-blue-500" />
          <h1 className="text-2xl font-bold text-gray-900">My Service</h1>
          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
            {resources.length}
          </span>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchResources} className="btn-secondary">
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </button>
          <button onClick={() => setShowCreateModal(true)} className="btn-primary">
            <Plus className="h-4 w-4 mr-1" /> Create
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {resources.map(r => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{r.name}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={r.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button className="text-red-600 hover:text-red-800"><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {resources.length === 0 && (
          <div className="text-center py-12 text-gray-500">No resources found</div>
        )}
      </div>
    </div>
  );
};

export default MyServicePage;
```

---

### API Client Pattern
**All API clients use `apiClient` from `./client` — never create raw axios instances:**

```typescript
// src/api/myservice.ts
import { apiClient } from './client';
import { getCurrentProject } from './client';

export interface MyResource {
  id: string;
  name: string;
}

export interface CreateMyResourceRequest {
  name: string;
  zone?: string;
}

// Always use /compute/v1/projects/{project}/... path pattern
export const listMyResources = async (project: string): Promise<MyResource[]> => {
  const response = await apiClient.get(
    `/compute/v1/projects/${project}/zones/us-central1-a/myresources`
  );
  return response.data.items || [];
};

export const createMyResource = async (
  project: string,
  data: CreateMyResourceRequest
): Promise<MyResource> => {
  const response = await apiClient.post(
    `/compute/v1/projects/${project}/zones/us-central1-a/myresources`,
    data
  );
  return response.data;
};

export const deleteMyResource = async (project: string, name: string): Promise<void> => {
  await apiClient.delete(
    `/compute/v1/projects/${project}/zones/us-central1-a/myresources/${name}`
  );
};
```

---

### Modal Pattern
**Use existing `Modal` component from `../components/Modal`:**

```tsx
import { Modal } from '../components/Modal';
import { FormField, Input } from '../components/FormFields';

// Inside component:
const [showCreateModal, setShowCreateModal] = useState(false);
const [formData, setFormData] = useState({ name: '' });

<Modal
  isOpen={showCreateModal}
  onClose={() => setShowCreateModal(false)}
  title="Create Resource"
>
  <form onSubmit={handleCreate} className="space-y-4">
    <FormField label="Name" required>
      <Input
        value={formData.name}
        onChange={e => setFormData({ ...formData, name: e.target.value })}
        placeholder="my-resource-name"
      />
    </FormField>
    <div className="flex justify-end gap-2 pt-4">
      <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">Cancel</button>
      <button type="submit" className="btn-primary">Create</button>
    </div>
  </form>
</Modal>
```

---

### Status Badge Pattern
```tsx
const StatusBadge = ({ status }: { status: string }) => {
  const colors: Record<string, string> = {
    RUNNING: 'bg-green-100 text-green-800',
    STOPPED: 'bg-gray-100 text-gray-800',
    PROVISIONING: 'bg-yellow-100 text-yellow-800',
    ERROR: 'bg-red-100 text-red-800',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
};
```

---

### Adding a New Page: Checklist

1. **Create page**: `src/pages/MyServicePage.tsx`
2. **Create API client**: `src/api/myservice.ts`
3. **Add route** in `src/App.tsx`:
   ```tsx
   import MyServicePage from './pages/MyServicePage';
   // In router:
   <Route path="/my-service" element={<MyServicePage />} />
   ```
4. **Add sidebar link** in the layout component (find existing sidebar in `src/layouts/`)
5. **Add service card** to `HomePage.tsx` if it's a new GCP service

---

## Tailwind Conventions Used in This Project

| Class | Usage |
|-------|-------|
| `p-6` | Page padding |
| `mb-6` | Bottom margin between sections |
| `bg-white rounded-lg shadow` | Card / table container |
| `text-2xl font-bold text-gray-900` | Page title |
| `text-xs font-medium text-gray-500 uppercase tracking-wider` | Table header |
| `hover:bg-gray-50` | Table row hover |
| `text-sm text-gray-600` | Muted body text |
| `text-red-600 hover:text-red-800` | Danger/delete action |
| `text-blue-500` | Icon accent color |

---

## Key Rules

- **Always** use `useProject()` for the current project — never hardcode project IDs
- **Always** handle `loading`, `error`, and empty states
- **Never** create raw `axios` instances — use `apiClient` from `./client`
- **Always** reset form state on modal close
- API errors: use `err.response?.data?.detail || 'fallback message'`
- Icon imports: always from `lucide-react`
- Use `formatDistanceToNow` (date-fns) for relative timestamps
