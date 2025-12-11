import Navbar from '../components/dashboard/Navbar';
import HeaderStats from '../components/dashboard/HeaderStats';
import ServiceCard from '../components/dashboard/ServiceCard';

const DashboardPage = () => {
  const services = [
    {
      name: 'Cloud Storage',
      icon: '☁️',
      status: 'Active' as const,
      path: '/services/storage',
    },
    {
      name: 'Compute Engine',
      icon: '⚙️',
      status: 'Coming Soon' as const,
    },
    {
      name: 'IAM',
      icon: '🔐',
      status: 'Active' as const,
      path: '/services/iam',
    },
    {
      name: 'Networking',
      icon: '🌐',
      status: 'Coming Soon' as const,
    },
    {
      name: 'Logging',
      icon: '📝',
      status: 'Coming Soon' as const,
    },
    {
      name: 'Monitoring',
      icon: '📊',
      status: 'Coming Soon' as const,
    },
  ];

  return (
    <div className="min-h-screen bg-[#f5f7fa]">
      <Navbar />

      <main className="max-w-6xl mx-auto px-8 py-10">
        {/* Header Stats */}
        <HeaderStats />

        {/* Services Section */}
        <section className="space-y-4">
          <div className="flex flex-col gap-2">
            <h2 className="text-2xl font-semibold text-gray-900">Available Services</h2>
            <p className="text-sm text-gray-600">Core emulator surfaces with status and quick navigation.</p>
          </div>

          <div className="bg-[#f9fafb] border border-gray-200 rounded-2xl p-8 shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {services.map((service) => (
                <ServiceCard
                  key={service.name}
                  name={service.name}
                  icon={service.icon}
                  status={service.status}
                  path={service.path}
                />
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardPage;
