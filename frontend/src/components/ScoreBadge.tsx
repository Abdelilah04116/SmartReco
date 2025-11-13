interface ScoreBadgeProps {
  label: 'high' | 'medium' | 'low';
  score?: number;
}

const ScoreBadge = ({ label, score }: ScoreBadgeProps) => {
  const styles = {
    high: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-amber-100 text-amber-800 border-amber-300',
    low: 'bg-red-100 text-red-800 border-red-300',
  };

  const labelText = {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[label]}`}
    >
      {labelText[label]}
      {score !== undefined && (
        <span className="ml-1">({score.toFixed(1)})</span>
      )}
    </span>
  );
};

export default ScoreBadge;


