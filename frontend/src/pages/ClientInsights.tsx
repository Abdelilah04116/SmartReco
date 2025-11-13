import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ScoreBadge from '../components/ScoreBadge';
import { apiService, CustomerDetailResponse } from '../services/api';

const ClientInsights = () => {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CustomerDetailResponse | null>(null);

  useEffect(() => {
    if (customerId) {
      loadCustomerDetail();
    }
  }, [customerId]);

  const loadCustomerDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getCustomerDetail(customerId!);
      setData(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load customer details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading customer details...</div>;
  }

  if (error || !data) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error || 'Customer not found'}
      </div>
    );
  }

  const { customer, suggested_action } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-primary-600 hover:text-primary-700 mb-4"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Customer Insights</h1>
          <p className="text-gray-600 mt-1">Detailed analysis for {customer.customer_id}</p>
        </div>
        <ScoreBadge label={customer.priority_label} score={customer.priority_score} />
      </div>

      {/* Priority Score Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Priority Score</h2>
        <div className="flex items-center space-x-4">
          <div className="text-4xl font-bold text-primary-600">
            {customer.priority_score.toFixed(2)}
          </div>
          <div>
            <p className="text-sm text-gray-600">Priority Label</p>
            <ScoreBadge label={customer.priority_label} />
          </div>
        </div>
      </div>

      {/* Suggested Action */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-2 text-blue-900">Suggested Action</h2>
        <p className="text-blue-800">{suggested_action}</p>
      </div>

      {/* Rules Fired */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Rules Fired ({customer.rules_fired.length})</h2>
        <div className="space-y-3">
          {customer.rules_fired.map((rule, index) => (
            <div
              key={index}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{rule.rule_label}</h3>
                  <p className="text-sm text-gray-600 mt-1">{rule.reason}</p>
                </div>
                <div className="ml-4 text-right">
                  <div className="text-2xl font-bold text-primary-600">+{rule.points}</div>
                  <div className="text-xs text-gray-500">points</div>
                </div>
              </div>
            </div>
          ))}
          {customer.rules_fired.length === 0 && (
            <p className="text-gray-500 text-center py-4">No rules fired for this customer</p>
          )}
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Score Breakdown</h2>
        <div className="space-y-2">
          {Object.entries(customer.explain.score_breakdown || {}).map(([ruleId, points]) => (
            <div key={ruleId} className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-700">{ruleId}</span>
              <span className="font-semibold text-primary-600">+{typeof points === 'number' ? points : String(points)}</span>
            </div>
          ))}
          <div className="flex justify-between items-center py-2 font-bold text-lg border-t-2 mt-2">
            <span>Total Score</span>
            <span className="text-primary-600">{customer.priority_score.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Raw Data */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Customer Data</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(customer.raw_data).map(([key, value]) => (
            <div key={key}>
              <p className="text-sm text-gray-600 capitalize">{key.replace('_', ' ')}</p>
              <p className="font-semibold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString() : String(value)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClientInsights;

