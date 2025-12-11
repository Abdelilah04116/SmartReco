import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import DataTable from '../components/DataTable';
import KpiCard from '../components/KpiCard';
import apiService from '../services/api';
import DatasetSelector from '../components/DatasetSelector';
import ExportButtons from '../components/ExportButtons';
import ShareButton from '../components/ShareButton';
import FreshnessTag from '../components/FreshnessTag';
import RuleConfigPanel from '../components/RuleConfigPanel';

const LAST_FILE_KEY = 'smartreco:lastFileId';

const Recommendations = () => {
  const [fileId, setFileId] = useState('');
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [datasetMeta, setDatasetMeta] = useState<{ created_at?: string } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(LAST_FILE_KEY);
    if (stored) {
      setFileId(stored);
    }
  }, []);

  useEffect(() => {
    if (fileId) {
      loadRecommendations(fileId);
    }
  }, [fileId]);

  const loadRecommendations = async (fileId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [res, preview] = await Promise.all([
        apiService.getRecommendations(fileId),
        apiService.getDatasetPreview(fileId).catch(() => null),
      ]);
      setResponse(res);
      if (preview) {
        setDatasetMeta({ created_at: preview.created_at });
      }
      localStorage.setItem(LAST_FILE_KEY, fileId);
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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Recommandations Clients</h1>
            {datasetMeta?.created_at && (
              <div className="mt-2">
                <FreshnessTag createdAt={datasetMeta.created_at} />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <ExportButtons fileId={fileId} tableType="recommendations" disabled={!fileId || !response} />
            <ShareButton fileId={fileId} disabled={!fileId || !response} />
          </div>
        </div>
        <div className="mb-6 flex flex-col gap-2">
          <DatasetSelector onSelect={setFileId} current={fileId} />
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
          <>
            {response && (
              <div className="mb-6">
                <RuleConfigPanel fileId={fileId} onUpdate={() => fileId && loadRecommendations(fileId)} />
              </div>
            )}
            <div className="bg-white rounded-lg shadow">
              <DataTable data={response?.actions || response?.customers || []} />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Recommendations;

