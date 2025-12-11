import { RuleCandidate } from '../services/api';

interface Props {
  rules: RuleCandidate[];
}

const severityColor: Record<string, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-green-100 text-green-700',
};

const RulesPanel = ({ rules }: Props) => {
  if (!rules.length) return null;
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-3">5. Business rule candidates</h2>
      <div className="space-y-3">
        {rules.map((rule, idx) => (
          <div key={idx} className="p-4 border rounded-lg bg-slate-50">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-slate-900">{rule.rule}</p>
              <span className={`text-xs px-2 py-1 rounded ${severityColor[rule.severity] || 'bg-slate-200'}`}>
                {rule.severity}
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-1">{rule.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RulesPanel;


