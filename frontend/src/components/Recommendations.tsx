import { RecommendationItem, RuleCandidate } from '../services/api';

interface Props {
  insights: string;
  actions: RecommendationItem[];
  rules: RuleCandidate[];
}

const Recommendations = ({ insights, actions, rules }: Props) => {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-2">6. Recommendations</h2>
      <p className="text-sm text-slate-600 mb-4">{insights}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 border rounded-lg bg-slate-50">
          <p className="font-semibold text-slate-900 mb-2">Prioritized actions</p>
          <ul className="space-y-2 text-sm text-slate-700">
            {actions.map((action) => (
              <li key={action.title} className="border-b pb-2 last:border-b-0 last:pb-0">
                <span className="font-semibold">{action.title}</span> – {action.description} (
                <span className="uppercase">{action.priority}</span>)
              </li>
            ))}
          </ul>
        </div>
        <div className="p-4 border rounded-lg bg-slate-50">
          <p className="font-semibold text-slate-900 mb-2">Business rules supporting actions</p>
          <ul className="space-y-2 text-sm text-slate-700">
            {rules.map((rule, idx) => (
              <li key={idx}>
                <span className="font-semibold">{rule.rule}</span> – {rule.rationale}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;




