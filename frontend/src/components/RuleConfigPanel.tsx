import { useState } from 'react';
import apiService from '../services/api';

interface RuleConfigPanelProps {
  fileId: string | null;
  onUpdate?: () => void;
}

const RuleConfigPanel = ({ fileId, onUpdate }: RuleConfigPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [thresholds, setThresholds] = useState<Record<string, number>>({});
  const [multipliers, setMultipliers] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!fileId) return;

    setSaving(true);
    try {
      await apiService.configureRules({
        file_id: fileId,
        weights,
        thresholds,
        multipliers,
      });
      alert('Configuration sauvegardée! Les recommandations seront recalculées.');
      onUpdate?.();
    } catch (err) {
      console.error('Failed to save config:', err);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800">Configuration des Règles</h3>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {isOpen ? 'Réduire' : 'Ouvrir'}
        </button>
      </div>

      {isOpen && (
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Poids des règles</h4>
            <div className="space-y-2">
              {Object.entries(weights).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="text-sm w-32">{key}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={value}
                    onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })}
                    className="flex-1 px-2 py-1 border rounded"
                  />
                </div>
              ))}
              <button
                onClick={() => {
                  const key = prompt('Nom de la règle:');
                  if (key) setWeights({ ...weights, [key]: 1.0 });
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                + Ajouter un poids
              </button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Seuils</h4>
            <div className="space-y-2">
              {Object.entries(thresholds).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="text-sm w-32">{key}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={value}
                    onChange={(e) => setThresholds({ ...thresholds, [key]: Number(e.target.value) })}
                    className="flex-1 px-2 py-1 border rounded"
                  />
                </div>
              ))}
              <button
                onClick={() => {
                  const key = prompt('Nom du seuil:');
                  if (key) setThresholds({ ...thresholds, [key]: 0.5 });
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                + Ajouter un seuil
              </button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Multiplicateurs</h4>
            <div className="space-y-2">
              {Object.entries(multipliers).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="text-sm w-32">{key}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={value}
                    onChange={(e) => setMultipliers({ ...multipliers, [key]: Number(e.target.value) })}
                    className="flex-1 px-2 py-1 border rounded"
                  />
                </div>
              ))}
              <button
                onClick={() => {
                  const key = prompt('Nom du multiplicateur:');
                  if (key) setMultipliers({ ...multipliers, [key]: 1.0 });
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                + Ajouter un multiplicateur
              </button>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={saving || !fileId}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
          >
            {saving ? 'Sauvegarde...' : 'Sauvegarder et Recalculer'}
          </button>
        </div>
      )}
    </div>
  );
};

export default RuleConfigPanel;

