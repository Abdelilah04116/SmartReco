import { useState, useEffect } from 'react';
import { apiService, AIAnalysisResponse } from '../services/api';

interface AIRecommendationsProps {
  onChartsSelected?: (chartTypes: string[]) => void;
}

const AIRecommendations = ({ onChartsSelected }: AIRecommendationsProps) => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AIAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAIAnalysis();
  }, []);

  const loadAIAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getAIAnalysis();
      setAnalysis(data);
      
      // Auto-select recommended charts
      if (data.suggested_charts && data.suggested_charts.length > 0 && onChartsSelected) {
        const recommendedTypes = data.suggested_charts
          .filter(chart => chart.priority === 'high')
          .map(chart => chart.type);
        if (recommendedTypes.length > 0) {
          onChartsSelected(recommendedTypes);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load AI analysis');
      console.error('AI analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          <span className="text-gray-600">AI Agent is analyzing your data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm">
          AI analysis unavailable: {error}. Using default recommendations.
        </p>
      </div>
    );
  }

  if (!analysis || !analysis.ai_enabled) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-blue-800 text-sm">
          AI Agent is not configured. Using default analysis.
        </p>
      </div>
    );
  }

  const { recommendations, suggested_charts, feature_engineering_suggestions, transformation_plan } = analysis;

  return (
    <div className="space-y-4">
      {/* AI Insights */}
      {recommendations?.insights && recommendations.insights.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-3">
            <span className="text-2xl">🤖</span>
            <h3 className="text-lg font-bold text-gray-900">AI Insights</h3>
          </div>
          <ul className="space-y-2">
            {recommendations.insights.map((insight: string, index: number) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-primary-600 mt-1">•</span>
                <span className="text-gray-700">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Charts */}
      {suggested_charts && suggested_charts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <span>📊</span>
            <span>Recommended Visualizations</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggested_charts.map((chart, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 ${
                  chart.priority === 'high' ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold capitalize">{chart.type} Chart</span>
                  {chart.priority === 'high' && (
                    <span className="px-2 py-1 bg-primary-600 text-white text-xs rounded">Recommended</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-2">{chart.reason}</p>
                {chart.columns && chart.columns.length > 0 && (
                  <p className="text-xs text-gray-500">
                    Columns: {chart.columns.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Cleaning Recommendations */}
      {recommendations?.data_cleaning && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <span>🧹</span>
            <span>Data Cleaning Recommendations</span>
          </h3>
          <div className="space-y-2 text-sm">
            {recommendations.data_cleaning.handle_missing_values && (
              <div className="flex items-center space-x-2">
                <span className="text-green-600">✓</span>
                <span>
                  Missing values: {recommendations.data_cleaning.handle_missing_values}
                  {recommendations.data_cleaning.imputation_method && 
                    ` (${recommendations.data_cleaning.imputation_method})`}
                </span>
              </div>
            )}
            {recommendations.data_cleaning.normalization_needed && (
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">✓</span>
                <span>
                  Normalization: {recommendations.data_cleaning.normalization_method || 'standard'}
                </span>
              </div>
            )}
            {recommendations.data_cleaning.outlier_handling && (
              <div className="flex items-center space-x-2">
                <span className="text-orange-600">✓</span>
                <span>Outlier handling: {recommendations.data_cleaning.outlier_handling}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Feature Engineering Suggestions */}
      {feature_engineering_suggestions && feature_engineering_suggestions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <span>⚙️</span>
            <span>Feature Engineering Suggestions</span>
          </h3>
          <div className="space-y-3">
            {feature_engineering_suggestions.map((suggestion, index) => (
              <div key={index} className="border-l-4 border-primary-500 pl-4">
                <div className="font-semibold text-sm capitalize">{suggestion.type}</div>
                <div className="text-sm text-gray-600 mt-1">{suggestion.formula}</div>
                <div className="text-xs text-gray-500 mt-1">{suggestion.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transformation Plan */}
      {transformation_plan && transformation_plan.steps && transformation_plan.steps.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <span>🔄</span>
            <span>Applied Transformations</span>
          </h3>
          <div className="space-y-2">
            {transformation_plan.steps.map((step: any, index: number) => (
              <div key={index} className="flex items-center space-x-2 text-sm">
                <span className="text-green-600">✓</span>
                <span>
                  {step.action}: {step.method || 'N/A'}
                  {step.columns && ` (${step.columns.length} columns)`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIRecommendations;

