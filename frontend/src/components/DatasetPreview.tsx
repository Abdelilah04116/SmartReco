import { ColumnSummary } from '../services/api';

interface Props {
  filename: string;
  rows: Record<string, any>[];
  dtypes: Record<string, string>;
  columns: ColumnSummary[];
}

const DatasetPreview = ({ filename, rows, columns }: Props) => {
  const sampleRows = rows.slice(0, 5);
  const headers = Object.keys(sampleRows[0] || {});

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">2. Dataset Preview</h2>
          <p className="text-sm text-slate-500">{filename}</p>
        </div>
        <p className="text-sm text-slate-500">Showing first {sampleRows.length} rows</p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-left border">
          <thead className="bg-slate-100">
            <tr>
              {headers.map((header) => (
                <th key={header} className="px-3 py-2 border-b text-slate-700">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sampleRows.map((row, idx) => (
              <tr key={idx} className="border-b">
                {headers.map((header) => (
                  <td key={header} className="px-3 py-2 text-slate-700">
                    {String(row[header] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-xs">
        {columns.map((col) => (
          <div key={col.name} className="p-3 border rounded-lg bg-slate-50">
            <p className="font-semibold text-slate-800">{col.name}</p>
            <p className="text-slate-500">Type: {col.dtype}</p>
            <p className="text-slate-500">Unique: {col.unique}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DatasetPreview;




