import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './contexts/AppContext';
import CloudConsoleLayout from './layouts/CloudConsoleLayout';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import PlaceholderServicePage from './pages/PlaceholderServicePage';
import StorageDashboardPage from './pages/StorageDashboardPage';
import BucketListPage from './pages/BucketListPage';
import BucketDetails from './pages/BucketDetails';
import ObjectDetailsPage from './pages/ObjectDetailsPage';
import ActivityPage from './pages/ActivityPage';
import EventsPage from './pages/EventsPage';
import SettingsPage from './pages/SettingsPage';
import IAMDashboard from './pages/IAMDashboard';
import LifecycleRulesPage from './pages/LifecycleRulesPage';
import NotificationsPage from './pages/NotificationsPage';

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          {/* New Dashboard - Standalone without CloudConsoleLayout */}
          <Route path="/" element={<DashboardPage />} />

          {/* Legacy home page */}
          <Route path="/legacy" element={<CloudConsoleLayout />}>
            <Route index element={<HomePage />} />
          </Route>

          {/* Service Routes */}
          <Route path="/services/:serviceName" element={<PlaceholderServicePage />} />

          {/* Cloud Storage Service Routes */}
          <Route path="/services/storage" element={<CloudConsoleLayout />}>
            <Route index element={<StorageDashboardPage />} />
            <Route path="buckets" element={<BucketListPage />} />
            <Route path="buckets/:bucketName" element={<BucketDetails />} />
            <Route path="buckets/:bucketName/objects/:objectName" element={<ObjectDetailsPage />} />
            <Route path="activity" element={<EventsPage />} />
            <Route path="lifecycle" element={<LifecycleRulesPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* IAM Service Routes */}
          <Route path="/services/iam" element={<CloudConsoleLayout />}>
            <Route index element={<IAMDashboard />} />
            <Route path="service-accounts" element={<IAMDashboard />} />
            <Route path="roles" element={<IAMDashboard />} />
            <Route path="policies" element={<IAMDashboard />} />
          </Route>

          {/* Legacy Routes - Redirect to new structure */}
          <Route path="/buckets" element={<Navigate to="/services/storage/buckets" replace />} />
          <Route path="/events" element={<Navigate to="/services/storage/activity" replace />} />
          <Route path="/settings" element={<Navigate to="/services/storage/settings" replace />} />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
