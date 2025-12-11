import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import KpiCard from '../components/KpiCard';
import Navbar from '../components/Navbar';
import apiService, { TemplateDescriptor } from '../services/api';
import DatasetSelector from '../components/DatasetSelector';
import SystemHealthBar from '../components/SystemHealthBar';
import DrilldownModal from '../components/DrilldownModal';
import DataFilters from '../components/DataFilters';
import ExportButtons from '../components/ExportButtons';
import ShareButton from '../components/ShareButton';
import TemplateSelector from '../components/TemplateSelector';
import FreshnessTag from '../components/FreshnessTag';

const LAST_FILE_KEY = 'smartreco:lastFileId';

interface DashboardWidget {
  id: string;
  type: 'kpi' | 'bar' | 'line' | 'pie' | 'area' | 'table';
  title: string;
  data: any;
  config?: any;
  position: { x: number; y: number; w: number; h: number };
  column?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const Dashboard = () => {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [loading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState(false);
  const [expandedWidget, setExpandedWidget] = useState<DashboardWidget | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDescriptor | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [datasetData, setDatasetData] = useState<any[]>([]);
  const [columns, setColumns] = useState<Array<{ name: string; dtype: string }>>([]);
  const [drilldownState, setDrilldownState] = useState<{ column: string; value?: any; chartType?: 'bar' | 'pie' | 'line' | 'area' } | null>(null);
  const [datasetMeta, setDatasetMeta] = useState<{ created_at?: string } | null>(null);

  useEffect(() => {
    checkDataAvailability();
  }, []);

  useEffect(() => {
    if (fileId) {
      loadDatasetData();
    }
  }, [fileId]);

  const checkDataAvailability = async () => {
    try {
      const stored = localStorage.getItem(LAST_FILE_KEY);
      if (stored) {
        setFileId(stored);
        setHasData(true);
        return;
      }

      const health = await apiService.healthCheck();
      if (health.last_file_id) {
        localStorage.setItem(LAST_FILE_KEY, health.last_file_id);
        setFileId(health.last_file_id);
      }
      setHasData(Boolean(health.dataset_loaded));
    } catch (err) {
      console.error('Error checking data:', err);
    }
  };

  const loadDatasetData = async () => {
    if (!fileId) return;
    try {
      const preview = await apiService.getDatasetPreview(fileId);
      setDatasetMeta({ created_at: preview.created_at });
      setColumns(preview.columns.map((c) => ({ name: c.name, dtype: c.dtype })));
      setDatasetData(preview.rows);
    } catch (err) {
      console.error('Failed to load dataset:', err);
    }
  };

  const generateDashboardFragment = async () => {
    try {
      setGenerating(true);
      setError(null);
      
      const fragment = await apiService.generateDashboardFragment();
      
      let newWidgets = fragment.widgets.map((w: any, index: number) => ({
        ...w,
        position: {
          x: (index % 3) * 4,
          y: Math.floor(index / 3) * 4,
          w: 4,
          h: 4
        },
        column: w.config?.column || (w.data?.[0]?.name ? 'name' : undefined),
      }));

      if (selectedTemplate) {
        const templateWidgets = selectedTemplate.layout.widgets || [];
        newWidgets = newWidgets.filter((w: any) => templateWidgets.includes(w.id));
      }
      
      setWidgets([...widgets, ...newWidgets]);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la génération du dashboard');
    } finally {
      setGenerating(false);
    }
  };

  const handleChartClick = (widget: DashboardWidget, data: any, chartType: 'bar' | 'pie' | 'line' | 'area') => {
    if (!widget.column) return;
    const value = data.name || data.value;
    setDrilldownState({ column: widget.column, value, chartType });
  };

  const renderWidgetContent = (widget: DashboardWidget, height = 300, enableClick = true) => {
    const handleBarClick = (data: any) => {
      if (enableClick) handleChartClick(widget, data, 'bar');
    };

    const handlePieClick = (data: any) => {
      if (enableClick) handleChartClick(widget, { name: data.name, value: data.value }, 'pie');
    };

    const handleLineClick = (data: any) => {
      if (enableClick) handleChartClick(widget, data, 'line');
    };

    switch (widget.type) {
      case 'kpi':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <KpiCard
              title={widget.config?.subtitle || ''}
              value={widget.data.value || 0}
              subtitle={widget.config?.unit}
              trend={widget.data.trend}
            />
          </div>
        );

      case 'bar':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <ResponsiveContainer width="100%" height={height}>
              <BarChart data={widget.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#0088FE" onClick={handleBarClick} style={{ cursor: 'pointer' }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'line':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <ResponsiveContainer width="100%" height={height}>
              <LineChart data={widget.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#0088FE" 
                  strokeWidth={2}
                  onClick={handleLineClick}
                  style={{ cursor: 'pointer' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'pie':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <ResponsiveContainer width="100%" height={height}>
              <PieChart>
                <Pie
                  data={widget.data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={handlePieClick}
                >
                  {widget.data.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      case 'area':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <ResponsiveContainer width="100%" height={height}>
              <AreaChart data={widget.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#0088FE" 
                  fill="#0088FE" 
                  fillOpacity={0.6}
                  onClick={handleLineClick}
                  style={{ cursor: 'pointer' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        );

      case 'table':
        return (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{widget.title}</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {widget.config?.columns?.map((col: string) => (
                      <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {widget.data.slice(0, 10).map((row: any, idx: number) => (
                    <tr key={idx}>
                      {widget.config?.columns?.map((col: string) => (
                        <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {row[col]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderWidget = (widget: DashboardWidget) => (
    <div key={widget.id} className="cursor-zoom-in" onClick={() => setExpandedWidget(widget)}>
      {renderWidgetContent(widget)}
    </div>
  );

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  const content = (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center flex-wrap gap-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard Dynamique</h1>
            <p className="text-gray-600 mt-2">Visualisez vos données avec des widgets générés par IA</p>
            <div className="mt-2 flex items-center gap-2">
              <SystemHealthBar />
              {datasetMeta?.created_at && <FreshnessTag createdAt={datasetMeta.created_at} />}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <DatasetSelector onSelect={(id) => { setFileId(id); setHasData(true); }} current={fileId} />
            <ShareButton fileId={fileId} disabled={!hasData} />
            <button
              onClick={toggleFullscreen}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg shadow-md transition-colors"
              title="Mode plein écran"
            >
              {isFullscreen ? '⤓' : '⛶'}
            </button>
          </div>
        </div>

        <div className="mb-6 flex justify-between items-center flex-wrap gap-4">
          <TemplateSelector onSelect={setSelectedTemplate} selected={selectedTemplate?.id} />
          <button
            onClick={generateDashboardFragment}
            disabled={generating || !hasData}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition-colors flex items-center gap-2"
          >
            {generating ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Génération...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Générer un Fragment de Dashboard
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {!hasData && (
          <div className="mb-6 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
            Aucune donnée disponible. Veuillez d'abord uploader un dataset via la page Overview.
          </div>
        )}

        {columns.length > 0 && datasetData.length > 0 && (
          <DataFilters
            columns={columns}
            data={datasetData}
            onFilterChange={(filtered) => {
              // Filtered data can be used here for future enhancements
              console.log('Filtered data:', filtered.length, 'rows');
            }}
          />
        )}

        {widgets.length === 0 && !loading && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun widget</h3>
            <p className="mt-1 text-sm text-gray-500">Cliquez sur "Générer un Fragment de Dashboard" pour commencer</p>
          </div>
        )}

        {widgets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {widgets.map((widget) => renderWidget(widget))}
          </div>
        )}

        {expandedWidget && (
          <div
            className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
            onClick={() => setExpandedWidget(null)}
          >
            <div
              className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between px-6 pt-4">
                <h3 className="text-xl font-semibold text-gray-900">{expandedWidget.title}</h3>
                <div className="flex items-center gap-2">
                  <ExportButtons fileId={fileId} plotId={expandedWidget.id} disabled={!fileId} />
                  <button
                    onClick={() => setExpandedWidget(null)}
                    className="text-gray-500 hover:text-gray-700"
                    aria-label="Fermer"
                  >
                    ✕
                  </button>
                </div>
              </div>
              <div className="p-6">
                {renderWidgetContent(expandedWidget, 520, false)}
              </div>
            </div>
          </div>
        )}

        {drilldownState && (
          <DrilldownModal
            isOpen={!!drilldownState}
            onClose={() => setDrilldownState(null)}
            fileId={fileId}
            column={drilldownState.column}
            value={drilldownState.value}
            chartType={drilldownState.chartType}
          />
        )}
      </div>
    </div>
  );

  return content;
};

export default Dashboard;
