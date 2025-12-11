interface StatCardProps {
  title: string;
  value: string;
  showStatusDot?: boolean;
}

const StatCard = ({ title, value, showStatusDot }: StatCardProps) => {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-md px-6 py-5 w-full min-w-[240px] min-h-[110px] flex flex-col justify-center gap-2">
      <div className="text-xs font-semibold tracking-wide text-gray-500 uppercase">{title}</div>
      <div className="flex items-center gap-3">
        {showStatusDot && <div className="w-2.5 h-2.5 bg-green-500 rounded-full"></div>}
        <div className="text-2xl font-bold text-gray-900 leading-tight">{value}</div>
      </div>
    </div>
  );
};

const HeaderStats = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
      <StatCard title="Service Status" value="Running" showStatusDot />
      <StatCard title="Version" value="0.1.0" />
      <StatCard title="Storage Backend" value="Postgres" />
    </div>
  );
};

export default HeaderStats;
