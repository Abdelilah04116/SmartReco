import { useEffect, useState } from 'react';
import apiService, { DatasetMeta } from '../services/api';

const LAST_FILE_KEY = 'smartreco:lastFileId';

interface Props {
  onSelect: (fileId: string) => void;
  current?: string | null;
  showBadge?: boolean;
}

const DatasetSelector = ({ onSelect, current, showBadge = true }: Props) => {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        setLoading(true);
        const res = await apiService.listDatasets();
        setDatasets(res.datasets || []);
        if (!current) {
          const stored = localStorage.getItem(LAST_FILE_KEY);
          if (stored) onSelect(stored);
        }
      } catch (err: any) {
        setError(err.message || 'Impossible de charger les datasets');
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, []);

  const handleChange = (value: string) => {
    localStorage.setItem(LAST_FILE_KEY, value);
    onSelect(value);
  };

  return (
    <div className="flex items-center gap-3">
      <div>
        <label className="text-sm text-gray-600 block mb-1">Dataset</label>
        <select
          className="border rounded px-3 py-2 min-w-[240px]"
          disabled={loading}
          value={current || ''}
          onChange={(e) => handleChange(e.target.value)}
        >
          <option value="" disabled>
            {loading ? 'Chargement...' : 'Sélectionner un dataset'}
          </option>
          {datasets.map((ds) => (
            <option key={ds.file_id} value={ds.file_id}>
              {ds.name} — {ds.rows}x{ds.columns}
            </option>
          ))}
        </select>
      </div>
      {showBadge && current && (
        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
          En cours
        </span>
      )}
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  );
};

export default DatasetSelector;

