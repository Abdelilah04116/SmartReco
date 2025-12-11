import { useState } from 'react';

interface ShareButtonProps {
  fileId: string | null;
  disabled?: boolean;
}

const ShareButton = ({ fileId, disabled }: ShareButtonProps) => {
  const [sharing, setSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const handleShare = async () => {
    if (!fileId || disabled) return;

    setSharing(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/share/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: fileId }),
      });
      if (response.ok) {
        const data = await response.json();
        const fullUrl = `${window.location.origin}/share/${data.token}`;
        setShareUrl(fullUrl);
        navigator.clipboard.writeText(fullUrl).then(() => {
          alert('Lien copié dans le presse-papiers!');
        });
      }
    } catch (err) {
      console.error('Share failed:', err);
      alert('Erreur lors de la création du lien');
    } finally {
      setSharing(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleShare}
        disabled={disabled || sharing}
        className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded disabled:opacity-50 flex items-center gap-2"
      >
        {sharing ? '⏳' : '🔗'} {sharing ? 'Création...' : 'Partager'}
      </button>
      {shareUrl && (
        <span className="text-xs text-gray-600 max-w-xs truncate" title={shareUrl}>
          {shareUrl}
        </span>
      )}
    </div>
  );
};

export default ShareButton;

