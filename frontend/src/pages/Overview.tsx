import { useEffect, useState } from 'react';
import { Alert, CircularProgress } from '@mui/material';

import FileUploader from '../components/FileUploader';
import DatasetPreview from '../components/DatasetPreview';
import PlotGallery from '../components/PlotGallery';
import FeaturesPanel from '../components/FeaturesPanel';
import RulesPanel from '../components/RulesPanel';
import Recommendations from '../components/Recommendations';
import Navbar from '../components/Navbar';
import apiService, {
  AnalyzeResponse,
  FeatureResponse,
  PlotResponse,
  RecommendationResponse,
  RuleResponse,
  UploadResponse,
} from '../services/api';

function Overview() {
  const [fileId, setFileId] = useState<string | null>(null);
  const [preview, setPreview] = useState<UploadResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [plots, setPlots] = useState<PlotResponse | null>(null);
  const [features, setFeatures] = useState<FeatureResponse | null>(null);
  const [rules, setRules] = useState<RuleResponse | null>(null);
  const [recs, setRecs] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fileId) return;
    const fetchAll = async () => {
      try {
        setLoading(true);
        setError(null);
        const [analysisRes, plotsRes, featureRes, rulesRes, recsRes] = await Promise.all([
          apiService.analyzeDataset(fileId),
          apiService.getPlots(fileId),
          apiService.getFeatures(fileId),
          apiService.getRules(fileId),
          apiService.getRecommendations(fileId),
        ]);
        setAnalysis(analysisRes);
        setPlots(plotsRes);
        setFeatures(featureRes);
        setRules(rulesRes);
        setRecs(recsRes);
      } catch (err: any) {
        setError(err.message || 'An error occurred while processing the dataset.');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [fileId]);

  const handleUpload = async (file: File) => {
    try {
      setLoading(true);
      const response = await apiService.uploadDataset(file);
      setPreview(response);
      setFileId(response.file_id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SmartReco</h1>
            <p className="text-sm text-slate-500">Agentic business recommendation system</p>
          </div>
          {loading && <CircularProgress size={24} />}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {error && <Alert severity="error">{error}</Alert>}

        <FileUploader onUpload={handleUpload} />

        {preview && (
          <DatasetPreview
            filename={preview.original_filename}
            rows={preview.rows}
            dtypes={preview.dtypes}
            columns={preview.columns}
          />
        )}

        {analysis && (
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">Dataset Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-700">
              <div className="p-3 border rounded-lg">
                <p className="font-semibold">Shape</p>
                <p>
                  {analysis.dataset_overview.row_count} rows / {analysis.dataset_overview.column_count} columns
                </p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="font-semibold">Numeric columns</p>
                <p>{analysis.dataset_overview.numeric_columns.join(', ') || 'None detected'}</p>
              </div>
              <div className="p-3 border rounded-lg">
                <p className="font-semibold">Categorical columns</p>
                <p>{analysis.dataset_overview.categorical_columns.join(', ') || 'None detected'}</p>
              </div>
            </div>
          </div>
        )}

        {plots && <PlotGallery plots={plots.plots} />}

        {features && <FeaturesPanel suggestions={features.suggestions} />}

        {rules && <RulesPanel rules={rules.rules} />}

        {recs && <Recommendations insights={recs.insights} actions={recs.actions} rules={recs.business_rules} />}
      </main>
    </div>
  );
}

export default Overview;

