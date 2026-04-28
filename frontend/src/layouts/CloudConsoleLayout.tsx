import { Outlet } from 'react-router-dom';
import CloudConsoleTopNav from '../components/navigation/CloudConsoleTopNav';

const CloudConsoleLayout = () => {
  return (
    <div className="flex h-screen bg-gray-50">
      <div className="flex-1 flex flex-col overflow-hidden">
        <CloudConsoleTopNav />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default CloudConsoleLayout;
