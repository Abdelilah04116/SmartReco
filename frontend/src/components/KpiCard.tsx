interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

const KpiCard = ({ title, value, subtitle, icon, trend }: KpiCardProps) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-primary-500 text-3xl">{icon}</div>
        )}
      </div>
      {trend && (
        <div className="mt-4">
          <span
            className={`text-xs ${
              trend === 'up'
                ? 'text-green-600'
                : trend === 'down'
                ? 'text-red-600'
                : 'text-gray-600'
            }`}
          >
            {trend === 'up' && '↑'} {trend === 'down' && '↓'} {trend === 'neutral' && '→'}
          </span>
        </div>
      )}
    </div>
  );
};

export default KpiCard;


