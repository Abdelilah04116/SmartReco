import { useEffect, useState } from 'react';
import apiService, { HealthCheckResponse } from '../services/api';

const SystemHealthBar = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);

  useEffect(() => {
    apiService.healthCheck().then(setHealth).catch(() => {});
  }, []);

  if (!health) return null;

  const pill = (label: string, value: string | number, color: string) => (
    <span className={`text-xs px-2 py-1 rounded-full ${color} bg-opacity-10 border ${color.replace('text', 'border')}`}>
      {label}: {value}
    </span>
  );

  return (
    <div className="flex flex-wrap gap-2 text-gray-700 text-xs">
      {pill('Datasets', health.dataset_count ?? 0, 'text-blue-600')}
      {pill('Rules', health.rules_loaded ?? 0, 'text-emerald-600')}
      {pill('Scored', health.scored_count ?? 0, 'text-purple-600')}
      {pill('Status', health.status, health.status === 'ok' ? 'text-green-600' : 'text-red-600')}
    </div>
  );
};

export default SystemHealthBar;

