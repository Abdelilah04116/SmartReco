import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import DataTable from '../components/DataTable';
import KpiCard from '../components/KpiCard';
// import ScoreBadge from '../components/ScoreBadge'; // supprimé car inutilisé
import apiService from '../services/api';

const Recommendations = () => {
  const [fileId, setFileId] = useState('');
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fileId) {
      loadRecommendations(fileId);
    }
  }, [fileId]);

  const loadRecommendations = async (fileId: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiService.getRecommendations(fileId);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des recommandations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Recommandations Clients</h1>
        <div className="mb-6">
          <input
            type="text"
            className="border px-3 py-2 rounded w-64"
            placeholder="Entrez un fileId de dataset..."
            value={fileId}
            onChange={e => setFileId(e.target.value)}
          />
          <span className="text-sm text-gray-400 ml-2">(copiez le fileId fourni à l'upload du dataset)</span>
        </div>
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        {response && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <KpiCard
              title="Total Actions"
              value={response.actions?.length || 0}
              trend="neutral"
            />
            <KpiCard
              title="Nb. Règles"
              value={response.business_rules?.length || 0}
              trend="neutral"
            />
            <KpiCard
              title="Insight"
              value={response.insights ? 1 : 0}
              trend="neutral"
            />
          </div>
        )}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow">
            <DataTable data={response?.actions || response?.customers || []} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Recommendations;

