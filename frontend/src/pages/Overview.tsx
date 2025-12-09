import { useState } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import KpiCard from '../components/KpiCard';
import RulesEditor from '../components/RulesEditor';
import { apiService, ScoreResponse } from '../services/api';

const Overview = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      await apiService.uploadDataset(file);
      setUploadStatus(`File "${file.name}" uploaded successfully`);
      
      // Auto-score after upload
      const scored = await apiService.scoreUploadedDataset();
      setScoreData(scored);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload file';
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSampleScoring = async () => {
    try {
      setLoading(true);
      setError(null);
      const scored = await apiService.scoreUploadedDataset();
      setScoreData(scored);
    } catch (err: any) {
      setError('No dataset uploaded. Please upload a CSV file first.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = scoreData
    ? [
        { name: 'High', value: scoreData.summary.high, color: '#10b981' },
        { name: 'Medium', value: scoreData.summary.medium, color: '#f59e0b' },
        { name: 'Low', value: scoreData.summary.low, color: '#ef4444' },
      ]
    : [];

  const barChartData = scoreData
    ? [
        { priority: 'High', count: scoreData.summary.high },
        { priority: 'Medium', count: scoreData.summary.medium },
        { priority: 'Low', count: scoreData.summary.low },
      ]
    : [];

  const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Overview</h1>
        <p className="text-gray-600">Upload and score customer data using business rules</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Upload Dataset</h2>
        <div className="flex items-center space-x-4">
          <label className="cursor-pointer">
            <span className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 inline-block">
              Choose CSV File
            </span>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
              disabled={loading}
            />
          </label>
          <button
            onClick={handleRunSampleScoring}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Run Scoring'}
          </button>
        </div>
        {uploadStatus && (
          <div className="mt-4 text-sm text-green-600">{uploadStatus}</div>
        )}
        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
      </div>

      {/* KPI Cards */}
      {scoreData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <KpiCard
              title="Total Customers"
              value={scoreData.total_scored}
              subtitle="Scored customers"
            />
            <KpiCard
              title="High Priority"
              value={scoreData.summary.high}
              subtitle={`${((scoreData.summary.high / scoreData.total_scored) * 100).toFixed(1)}% of total`}
            />
            <KpiCard
              title="Medium Priority"
              value={scoreData.summary.medium}
              subtitle={`${((scoreData.summary.medium / scoreData.total_scored) * 100).toFixed(1)}% of total`}
            />
            <KpiCard
              title="Low Priority"
              value={scoreData.summary.low}
              subtitle={`${((scoreData.summary.low / scoreData.total_scored) * 100).toFixed(1)}% of total`}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Priority Distribution (Bar)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="priority" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Priority Distribution (Pie)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {/* Rules Editor */}
      <RulesEditor />
    </div>
  );
};

export default Overview;

