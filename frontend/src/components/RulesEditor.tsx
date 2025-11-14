import { useState, useEffect } from 'react';
import { apiService, RuleConfig } from '../services/api';

const RulesEditor = () => {
  const [rules, setRules] = useState<RuleConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{ enabled?: boolean; points?: number; threshold?: number }>({});

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const response = await apiService.getRules();
      setRules(response.rules);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (rule: RuleConfig) => {
    setEditingRule(rule.id);
    setEditValues({
      enabled: rule.enabled,
      points: rule.points,
      threshold: rule.threshold,
    });
  };

  const cancelEdit = () => {
    setEditingRule(null);
    setEditValues({});
  };

  const saveRule = async (ruleId: string) => {
    try {
      await apiService.updateRule(ruleId, editValues);
      await loadRules();
      setEditingRule(null);
      setEditValues({});
    } catch (err: any) {
      setError(err.message || 'Failed to update rule');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading rules...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Business Rules Configuration</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-lg">{rule.label}</h3>
                <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-100 p-2 rounded">
                  Condition: {rule.condition}
                </div>
              </div>
              <div className="ml-4">
                {rule.enabled ? (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    Enabled
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                    Disabled
                  </span>
                )}
              </div>
            </div>

            {editingRule === rule.id ? (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Enabled
                  </label>
                  <input
                    type="checkbox"
                    checked={editValues.enabled ?? rule.enabled}
                    onChange={(e) =>
                      setEditValues({ ...editValues, enabled: e.target.checked })
                    }
                    className="rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Points
                  </label>
                  <input
                    type="number"
                    value={editValues.points ?? rule.points}
                    onChange={(e) =>
                      setEditValues({
                        ...editValues,
                        points: parseFloat(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    step="0.1"
                  />
                </div>
                {rule.threshold !== undefined && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Threshold
                    </label>
                    <input
                      type="number"
                      value={editValues.threshold ?? rule.threshold}
                      onChange={(e) =>
                        setEditValues({
                          ...editValues,
                          threshold: parseFloat(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      step="0.1"
                    />
                  </div>
                )}
                <div className="flex space-x-2">
                  <button
                    onClick={() => saveRule(rule.id)}
                    className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                  >
                    Save
                  </button>
                  <button
                    onClick={cancelEdit}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm">
                  <span className="font-medium">Points: </span>
                  <span className="text-primary-600">{rule.points}</span>
                  {rule.threshold !== undefined && (
                    <>
                      <span className="mx-2">|</span>
                      <span className="font-medium">Threshold: </span>
                      <span className="text-primary-600">{rule.threshold}</span>
                    </>
                  )}
                </div>
                <button
                  onClick={() => startEdit(rule)}
                  className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RulesEditor;



