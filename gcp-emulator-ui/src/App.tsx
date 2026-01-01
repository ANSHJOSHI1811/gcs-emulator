import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './contexts/AppContext';
import CloudConsoleLayout from './layouts/CloudConsoleLayout';
import HomePage from './pages/HomePage';
import PlaceholderServicePage from './pages/PlaceholderServicePage';
import StorageDashboardPage from './pages/StorageDashboardPage';
import BucketListPage from './pages/BucketListPage';
import BucketDetails from './pages/BucketDetails';
import ObjectDetailsPage from './pages/ObjectDetailsPage';
import ActivityPage from './pages/ActivityPage';
import EventsPage from './pages/EventsPage';
import SettingsPage from './pages/SettingsPage';
import ServiceAccountsPage from './pages/ServiceAccountsPage';
import RolesPage from './pages/RolesPage';
import ComputeInstancesPage from './pages/ComputeInstancesPage';

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CloudConsoleLayout />}>
            <Route index element={<HomePage />} />
            
            {/* Service Routes */}
            <Route path="/services/:serviceName" element={<PlaceholderServicePage />} />
            
            {/* Cloud Storage Service Routes */}
            <Route path="/services/storage">
              <Route index element={<StorageDashboardPage />} />
              <Route path="buckets" element={<BucketListPage />} />
              <Route path="buckets/:bucketName" element={<BucketDetails />} />
              <Route path="buckets/:bucketName/objects/:objectName" element={<ObjectDetailsPage />} />
              <Route path="activity" element={<EventsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* IAM Service Routes */}
            <Route path="/services/iam">
              <Route index element={<Navigate to="/services/iam/service-accounts" replace />} />
              <Route path="service-accounts" element={<ServiceAccountsPage />} />
              <Route path="roles" element={<RolesPage />} />
            </Route>

            {/* Compute Engine Routes */}
            <Route path="/services/compute">
              <Route index element={<Navigate to="/services/compute/instances" replace />} />
              <Route path="instances" element={<ComputeInstancesPage />} />
            </Route>

            {/* Legacy Routes - Redirect to new structure */}
            <Route path="/buckets" element={<Navigate to="/services/storage/buckets" replace />} />
            <Route path="/events" element={<Navigate to="/services/storage/activity" replace />} />
            <Route path="/settings" element={<Navigate to="/services/storage/settings" replace />} />
          </Route>
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
