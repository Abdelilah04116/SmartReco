import { useMemo } from 'react';

interface FreshnessTagProps {
  createdAt?: string;
  staleThresholdDays?: number;
}

const FreshnessTag = ({ createdAt, staleThresholdDays = 7 }: FreshnessTagProps) => {
  const { isStale, timeAgo } = useMemo(() => {
    if (!createdAt) return { isStale: false, timeAgo: 'Inconnu' };

    const created = new Date(createdAt);
    const now = new Date();
    const diffMs = now.getTime() - created.getTime();
    const diffDays = diffMs / (1000 * 60 * 60 * 24);
    const diffHours = diffMs / (1000 * 60 * 60);

    let timeAgo = '';
    if (diffDays >= 1) {
      timeAgo = `${Math.floor(diffDays)} jour${Math.floor(diffDays) > 1 ? 's' : ''}`;
    } else if (diffHours >= 1) {
      timeAgo = `${Math.floor(diffHours)} heure${Math.floor(diffHours) > 1 ? 's' : ''}`;
    } else {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      timeAgo = `${diffMins} minute${diffMins > 1 ? 's' : ''}`;
    }

    return {
      isStale: diffDays > staleThresholdDays,
      timeAgo: `Il y a ${timeAgo}`,
    };
  }, [createdAt, staleThresholdDays]);

  if (!createdAt) return null;

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
        isStale
          ? 'bg-yellow-100 text-yellow-800'
          : 'bg-green-100 text-green-800'
      }`}
      title={`Créé le ${new Date(createdAt).toLocaleString('fr-FR')}`}
    >
      {isStale && '⚠️ '}
      {timeAgo}
    </span>
  );
};

export default FreshnessTag;

