import ScoreBadge from './ScoreBadge';

interface DataTableProps {
  data: any[];
}

const DataTable = ({ data }: DataTableProps) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        Aucune donnée disponible
      </div>
    );
  }

  // Extraire les colonnes du premier élément
  const columns = Object.keys(data[0] || {});

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {col === 'priority_label' ? (
                    <ScoreBadge score={row.priority_score || 0} label={row[col]} />
                  ) : col === 'priority_score' ? (
                    <span className="font-semibold">{row[col]?.toFixed(2) || '0.00'}</span>
                  ) : typeof row[col] === 'object' ? (
                    JSON.stringify(row[col])
                  ) : (
                    String(row[col] || '-')
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;

