import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import apiService, { DatasetMeta } from '../services/api';

const LAST_FILE_KEY = 'smartreco:lastFileId';

const History = () => {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const res = await apiService.listDatasets();
      setDatasets(res.datasets || []);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement de l’historique');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const restore = async (fileId: string) => {
    try {
      await apiService.restoreAnalysis(fileId);
      localStorage.setItem(LAST_FILE_KEY, fileId);
      alert('Analyses restaurées pour ce dataset. Revenir sur Overview ou Dashboard.');
    } catch (err: any) {
      alert(err.message || 'Pas de cache disponible pour ce dataset');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-4">Historique des analyses</h1>
        {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Taille</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Créé</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading && (
                <tr>
                  <td className="px-6 py-4 text-sm text-gray-500" colSpan={4}>
                    Chargement...
                  </td>
                </tr>
              )}
              {!loading && datasets.length === 0 && (
                <tr>
                  <td className="px-6 py-4 text-sm text-gray-500" colSpan={4}>
                    Aucun dataset trouvé. Uploadez un CSV dans Overview.
                  </td>
                </tr>
              )}
              {datasets.map((ds) => (
                <tr key={ds.file_id}>
                  <td className="px-6 py-4 text-sm text-gray-900">{ds.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {ds.rows} lignes / {ds.columns} colonnes
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(ds.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <button
                      onClick={() => restore(ds.file_id)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Restaurer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default History;

