import { useState, useEffect } from 'react';

export interface FilterConfig {
  column: string;
  type: 'categorical' | 'numeric';
  values?: string[];
  min?: number;
  max?: number;
}

interface DataFiltersProps {
  columns: Array<{ name: string; dtype: string }>;
  data: any[];
  onFilterChange: (filteredData: any[]) => void;
}

const DataFilters = ({ columns, data, onFilterChange }: DataFiltersProps) => {
  const [filters, setFilters] = useState<Record<string, FilterConfig>>({});
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    applyFilters();
  }, [filters, data]);

  const applyFilters = () => {
    let filtered = [...data];

    Object.values(filters).forEach((filter) => {
      if (filter.type === 'categorical' && filter.values && filter.values.length > 0) {
        filtered = filtered.filter((row) => filter.values!.includes(String(row[filter.column])));
      } else if (filter.type === 'numeric') {
        if (filter.min !== undefined) {
          filtered = filtered.filter((row) => {
            const val = Number(row[filter.column]);
            return !isNaN(val) && val >= filter.min!;
          });
        }
        if (filter.max !== undefined) {
          filtered = filtered.filter((row) => {
            const val = Number(row[filter.column]);
            return !isNaN(val) && val <= filter.max!;
          });
        }
      }
    });

    onFilterChange(filtered);
  };

  const addFilter = (column: string, type: 'categorical' | 'numeric') => {
    const col = columns.find((c) => c.name === column);
    if (!col) return;

    if (type === 'categorical') {
      setFilters({
        ...filters,
        [column]: { column, type, values: [] },
      });
    } else {
      const numericValues = data.map((row) => Number(row[column])).filter((v) => !isNaN(v));
      const min = numericValues.length > 0 ? Math.min(...numericValues) : 0;
      const max = numericValues.length > 0 ? Math.max(...numericValues) : 100;
      setFilters({
        ...filters,
        [column]: { column, type, min, max },
      });
    }
  };

  const removeFilter = (column: string) => {
    const newFilters = { ...filters };
    delete newFilters[column];
    setFilters(newFilters);
  };

  const updateCategoricalFilter = (column: string, values: string[]) => {
    setFilters({
      ...filters,
      [column]: { ...filters[column], values },
    });
  };

  const updateNumericFilter = (column: string, min?: number, max?: number) => {
    setFilters({
      ...filters,
      [column]: { ...filters[column], min, max },
    });
  };

  const categoricalCols = columns.filter((c) => c.dtype !== 'numeric' && c.dtype !== 'float64' && c.dtype !== 'int64');
  const numericCols = columns.filter((c) => c.dtype === 'numeric' || c.dtype === 'float64' || c.dtype === 'int64');

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800">Filtres</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {isExpanded ? 'Réduire' : 'Étendre'}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Ajouter un filtre</label>
            <div className="flex gap-2 flex-wrap">
              {categoricalCols.map((col) => (
                <button
                  key={col.name}
                  onClick={() => addFilter(col.name, 'categorical')}
                  disabled={!!filters[col.name]}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
                >
                  {col.name} (cat)
                </button>
              ))}
              {numericCols.map((col) => (
                <button
                  key={col.name}
                  onClick={() => addFilter(col.name, 'numeric')}
                  disabled={!!filters[col.name]}
                  className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded disabled:opacity-50"
                >
                  {col.name} (num)
                </button>
              ))}
            </div>
          </div>

          {Object.values(filters).map((filter) => {
            const col = columns.find((c) => c.name === filter.column);
            if (!col) return null;

            if (filter.type === 'categorical') {
              const uniqueValues = [...new Set(data.map((row) => String(row[filter.column])).filter(Boolean))].slice(0, 50);
              return (
                <div key={filter.column} className="border rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{filter.column}</span>
                    <button
                      onClick={() => removeFilter(filter.column)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Supprimer
                    </button>
                  </div>
                  <div className="max-h-32 overflow-y-auto flex flex-wrap gap-2">
                    {uniqueValues.map((val) => (
                      <label key={val} className="flex items-center space-x-1">
                        <input
                          type="checkbox"
                          checked={filter.values?.includes(val) || false}
                          onChange={(e) => {
                            const current = filter.values || [];
                            const updated = e.target.checked
                              ? [...current, val]
                              : current.filter((v) => v !== val);
                            updateCategoricalFilter(filter.column, updated);
                          }}
                          className="rounded"
                        />
                        <span className="text-sm">{val}</span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            } else {
              const numericValues = data.map((row) => Number(row[filter.column])).filter((v) => !isNaN(v));
              const dataMin = numericValues.length > 0 ? Math.min(...numericValues) : 0;
              const dataMax = numericValues.length > 0 ? Math.max(...numericValues) : 100;
              return (
                <div key={filter.column} className="border rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{filter.column}</span>
                    <button
                      onClick={() => removeFilter(filter.column)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Supprimer
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-600">Min</label>
                      <input
                        type="number"
                        value={filter.min ?? dataMin}
                        min={dataMin}
                        max={dataMax}
                        onChange={(e) =>
                          updateNumericFilter(filter.column, Number(e.target.value), filter.max)
                        }
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600">Max</label>
                      <input
                        type="number"
                        value={filter.max ?? dataMax}
                        min={dataMin}
                        max={dataMax}
                        onChange={(e) =>
                          updateNumericFilter(filter.column, filter.min, Number(e.target.value))
                        }
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                  </div>
                </div>
              );
            }
          })}
        </div>
      )}

      {Object.keys(filters).length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <button
            onClick={() => setFilters({})}
            className="text-sm text-red-600 hover:text-red-800"
          >
            Effacer tous les filtres
          </button>
        </div>
      )}
    </div>
  );
};

export default DataFilters;

