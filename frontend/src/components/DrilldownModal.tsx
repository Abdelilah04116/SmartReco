import { useState, useEffect } from 'react';
import apiService, { DrilldownResponse } from '../services/api';

interface DrilldownModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileId: string | null;
  column: string;
  value?: any;
  chartType?: 'bar' | 'pie' | 'line' | 'area';
}

const DrilldownModal = ({ isOpen, onClose, fileId, column, value, chartType }: DrilldownModalProps) => {
  const [data, setData] = useState<DrilldownResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !fileId || !column) return;

    const fetchDrilldown = async () => {
      setLoading(true);
      setError(null);
      try {
        const payload: any = {
          file_id: fileId,
          column,
          limit: 200,
        };

        if (chartType === 'bar' || chartType === 'pie') {
          payload.values = [value];
        } else if (chartType === 'line' || chartType === 'area') {
          if (typeof value === 'number') {
            payload.min_value = value * 0.95;
            payload.max_value = value * 1.05;
          }
        }

        const result = await apiService.drilldown(payload);
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load drilldown data');
      } finally {
        setLoading(false);
      }
    };

    fetchDrilldown();
  }, [isOpen, fileId, column, value, chartType]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 pt-4 border-b">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">Drilldown: {column}</h3>
            {value !== undefined && (
              <p className="text-sm text-gray-500 mt-1">Valeur sélectionnée: {String(value)}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {data && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold text-blue-700">{data.count}</p>
                </div>
                {data.stats.min !== undefined && (
                  <>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Min</p>
                      <p className="text-2xl font-bold text-green-700">{data.stats.min?.toFixed(2)}</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Max</p>
                      <p className="text-2xl font-bold text-purple-700">{data.stats.max?.toFixed(2)}</p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg col-span-3">
                      <p className="text-sm text-gray-600">Moyenne</p>
                      <p className="text-2xl font-bold text-orange-700">{data.stats.mean?.toFixed(2)}</p>
                    </div>
                  </>
                )}
              </div>

              {data.rows.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold mb-3">Données ({data.rows.length} lignes affichées)</h4>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(data.rows[0]).map((key) => (
                            <th
                              key={key}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data.rows.map((row, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            {Object.entries(row).map(([key, val]) => (
                              <td key={key} className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                {String(val ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DrilldownModal;

