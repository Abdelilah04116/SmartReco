import { useState, useEffect, useCallback } from 'react';
import DataTable from '../components/DataTable';
import { apiService, CustomerScore, CampaignSimulationResponse } from '../services/api';

const Recommendations = () => {
  const [customers, setCustomers] = useState<CustomerScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topN, setTopN] = useState(50);
  const [simulation, setSimulation] = useState<CampaignSimulationResponse | null>(null);
  const [simulating, setSimulating] = useState(false);

  const loadRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getRecommendations(topN);
      setCustomers(response.customers);
    } catch (err: any) {
      setError(err.message || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, [topN]);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const handleSimulateCampaign = async () => {
    try {
      setSimulating(true);
      setError(null);
      const result = await apiService.simulateCampaign(topN);
      setSimulation(result);
    } catch (err: any) {
      setError(err.message || 'Failed to simulate campaign');
    } finally {
      setSimulating(false);
    }
  };

  const handleExportCSV = () => {
    if (customers.length === 0) return;

    const headers = ['Customer ID', 'Priority Score', 'Priority Label', 'Rules Fired Count', 'Age', 'Balance'];
    const rows = customers.map((c) => [
      c.customer_id,
      c.priority_score.toFixed(2),
      c.priority_label,
      c.rules_fired.length,
      c.raw_data?.age || 'N/A',
      c.raw_data?.balance || 'N/A',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recommendations_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Recommendations</h1>
        <p className="text-gray-600">Top priority customers for marketing campaigns</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Top N Customers
            </label>
            <input
              type="number"
              value={topN}
              onChange={(e) => setTopN(Math.max(1, parseInt(e.target.value) || 1))}
              className="px-3 py-2 border border-gray-300 rounded-md w-24"
              min="1"
              max="10000"
            />
          </div>
          <button
            onClick={loadRecommendations}
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={handleExportCSV}
            disabled={customers.length === 0}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            Export CSV
          </button>
          <button
            onClick={handleSimulateCampaign}
            disabled={simulating || customers.length === 0}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {simulating ? 'Simulating...' : 'Simulate Campaign'}
          </button>
        </div>
      </div>

      {/* Campaign Simulation Results */}
      {simulation && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Campaign Simulation Results</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Estimated Conversion Rate</p>
              <p className="text-2xl font-bold text-primary-600">
                {(simulation.estimated_conversion_rate * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Estimated Revenue</p>
              <p className="text-2xl font-bold text-green-600">
                ${simulation.estimated_revenue.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Customers</p>
              <p className="text-2xl font-bold text-gray-900">
                {simulation.total_customers}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">ROI</p>
              <p className="text-2xl font-bold text-purple-600">
                {simulation.kpis.roi?.toFixed(2)}x
              </p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="bg-green-50 p-3 rounded">
              <p className="text-sm text-gray-600">High Priority</p>
              <p className="text-lg font-semibold">{simulation.high_priority_count}</p>
            </div>
            <div className="bg-amber-50 p-3 rounded">
              <p className="text-sm text-gray-600">Medium Priority</p>
              <p className="text-lg font-semibold">{simulation.medium_priority_count}</p>
            </div>
            <div className="bg-red-50 p-3 rounded">
              <p className="text-sm text-gray-600">Low Priority</p>
              <p className="text-lg font-semibold">{simulation.low_priority_count}</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Data Table */}
      {loading ? (
        <div className="text-center py-12">Loading recommendations...</div>
      ) : (
        <DataTable data={customers} />
      )}

      {/* Summary */}
      {customers.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Summary</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Average Score</p>
              <p className="text-2xl font-bold">
                {(customers.reduce((sum, c) => sum + c.priority_score, 0) / customers.length).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">High Priority</p>
              <p className="text-2xl font-bold text-green-600">
                {customers.filter((c) => c.priority_label === 'high').length}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Rules Fired</p>
              <p className="text-2xl font-bold">
                {customers.reduce((sum, c) => sum + c.rules_fired.length, 0)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;

