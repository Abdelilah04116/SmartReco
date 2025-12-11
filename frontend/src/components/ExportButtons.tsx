import { useState } from 'react';

interface ExportButtonsProps {
  fileId: string | null;
  tableType?: 'recommendations' | 'rules' | 'dataset';
  plotId?: string;
  disabled?: boolean;
}

const ExportButtons = ({ fileId, tableType = 'recommendations', plotId, disabled }: ExportButtonsProps) => {
  const [exporting, setExporting] = useState<string | null>(null);

  const handleExport = async (format: 'csv' | 'excel' | 'pdf' | 'png') => {
    if (!fileId || disabled) return;

    setExporting(format);
    try {
      if (format === 'png' && plotId) {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/export/plot/${plotId}/png`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_id: fileId }),
        });
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `plot_${plotId}.png`;
          a.click();
          window.URL.revokeObjectURL(url);
        }
      } else {
        const endpoint = `/export/${format}`;
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_id: fileId, table_type: tableType }),
        });
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const ext = format === 'excel' ? 'xlsx' : format;
          a.download = `export_${fileId?.slice(0, 8)}.${ext}`;
          a.click();
          window.URL.revokeObjectURL(url);
        }
      }
    } catch (err) {
      console.error('Export failed:', err);
      alert('Erreur lors de l\'export');
    } finally {
      setExporting(null);
    }
  };

  if (plotId) {
    return (
      <button
        onClick={() => handleExport('png')}
        disabled={disabled || exporting === 'png'}
        className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50"
      >
        {exporting === 'png' ? 'Export...' : '📥 PNG'}
      </button>
    );
  }

  return (
    <div className="flex gap-2">
      <button
        onClick={() => handleExport('csv')}
        disabled={disabled || exporting === 'csv'}
        className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
      >
        {exporting === 'csv' ? 'Export...' : '📥 CSV'}
      </button>
      <button
        onClick={() => handleExport('excel')}
        disabled={disabled || exporting === 'excel'}
        className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50"
      >
        {exporting === 'excel' ? 'Export...' : '📥 Excel'}
      </button>
      <button
        onClick={() => handleExport('pdf')}
        disabled={disabled || exporting === 'pdf'}
        className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded disabled:opacity-50"
      >
        {exporting === 'pdf' ? 'Export...' : '📥 PDF'}
      </button>
    </div>
  );
};

export default ExportButtons;

