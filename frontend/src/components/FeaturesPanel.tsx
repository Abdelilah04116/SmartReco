import { FeatureSuggestion } from '../services/api';

interface Props {
  suggestions: FeatureSuggestion[];
}

const FeaturesPanel = ({ suggestions }: Props) => {
  if (!suggestions.length) return null;
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-3">4. Feature engineering ideas</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {suggestions.map((s) => (
          <div key={s.name} className="p-4 border rounded-lg bg-slate-50">
            <p className="font-semibold text-slate-900">{s.name}</p>
            <p className="text-sm text-slate-600">{s.description}</p>
            <p className="text-xs text-slate-500 mt-1">Columns: {s.columns.join(', ')}</p>
            {s.preview && (
              <pre className="text-xs bg-white border rounded mt-2 p-2 overflow-x-auto">
                {JSON.stringify(s.preview, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FeaturesPanel;




