import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './contexts/AppContext';
import Layout from './layouts/Layout';
import Dashboard from './pages/Dashboard';
import BucketListPage from './pages/BucketListPage';
import BucketDetails from './pages/BucketDetails';
import ObjectDetailsPage from './pages/ObjectDetailsPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="/buckets" element={<BucketListPage />} />
            <Route path="/buckets/:bucketName" element={<BucketDetails />} />
            <Route path="/buckets/:bucketName/objects/:objectName" element={<ObjectDetailsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
