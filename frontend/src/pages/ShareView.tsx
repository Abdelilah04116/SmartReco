import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';

const ShareView = () => {
  const { token } = useParams<{ token: string }>();
  const [snapshot, setSnapshot] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError('Token manquant');
      setLoading(false);
      return;
    }

    const loadSnapshot = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/share/${token}`);
        if (!response.ok) {
          throw new Error('Snapshot non trouvé ou expiré');
        }
        const data = await response.json();
        setSnapshot(data);
      } catch (err: any) {
        setError(err.message || 'Erreur lors du chargement');
      } finally {
        setLoading(false);
      }
    };

    loadSnapshot();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        </div>
      </div>
    );
  }

  const data = snapshot?.data || {};
  const recommendations = data.recommendations || {};
  const rules = data.rules || {};
  const plots = data.plots || {};

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
          <strong>Vue en lecture seule</strong> - Ce dashboard a été partagé. Créé le{' '}
          {snapshot?.created_at ? new Date(snapshot.created_at).toLocaleString('fr-FR') : 'N/A'}
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard Partagé</h1>

        {recommendations.insights && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Insights</h2>
            <p className="text-gray-700">{recommendations.insights}</p>
          </div>
        )}

        {recommendations.actions && recommendations.actions.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Actions Recommandées</h2>
            <ul className="space-y-2">
              {recommendations.actions.map((action: any, idx: number) => (
                <li key={idx} className="border-l-4 border-blue-500 pl-4">
                  <strong>{action.title}</strong>
                  <p className="text-sm text-gray-600">{action.description}</p>
                  <span className="text-xs text-gray-500">Priorité: {action.priority}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {rules.rules && rules.rules.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Règles Métier</h2>
            <ul className="space-y-2">
              {rules.rules.map((rule: any, idx: number) => (
                <li key={idx} className="border-l-4 border-green-500 pl-4">
                  <strong>{rule.rule}</strong>
                  <p className="text-sm text-gray-600">{rule.rationale}</p>
                  <span className="text-xs text-gray-500">Sévérité: {rule.severity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {plots.plots && plots.plots.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Graphiques</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plots.plots.map((plot: any, idx: number) => (
                <div key={idx} className="border rounded p-4">
                  <h3 className="font-semibold mb-2">{plot.title}</h3>
                  {plot.image_base64 && (
                    <img
                      src={`data:image/png;base64,${plot.image_base64}`}
                      alt={plot.title}
                      className="w-full"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShareView;

