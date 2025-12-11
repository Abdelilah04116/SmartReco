/** Minimal API client for SmartReco backend. */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ColumnSummary {
  name: string;
  dtype: string;
  non_nulls: number;
  unique: number;
  sample_values: any[];
}

export interface UploadResponse {
  file_id: string;
  original_filename: string;
  rows: Record<string, any>[];
  dtypes: Record<string, string>;
  columns: ColumnSummary[];
}

export interface AnalyzeResponse {
  file_id: string;
  column_types: Record<string, string>;
  descriptive_stats: Record<string, any>;
  correlation_insights: Array<{ pair: string[]; correlation: number; strength: string }>;
  suggested_plots: Array<{ title: string; plot_type: string; columns: string[] }>;
  dataset_overview: Record<string, any>;
}

export interface PlotResult {
  title: string;
  plot_type: string;
  image_base64: string;
  description?: string;
}

export interface PlotResponse {
  file_id: string;
  plots: PlotResult[];
}

export interface FeatureSuggestion {
  name: string;
  description: string;
  columns: string[];
  preview?: Record<string, any>;
}

export interface FeatureResponse {
  file_id: string;
  suggestions: FeatureSuggestion[];
}

export interface RuleCandidate {
  rule: string;
  rationale: string;
  severity: string;
}

export interface RuleResponse {
  file_id: string;
  rules: RuleCandidate[];
}

export interface RecommendationItem {
  title: string;
  description: string;
  priority: string;
}

export interface RecommendationResponse {
  file_id: string;
  insights: string;
  business_rules: RuleCandidate[];
  actions: RecommendationItem[];
}

const api = axios.create({
  baseURL: API_BASE_URL,
});

const asJson = async <T>(promise: Promise<any>): Promise<T> => {
  const res = await promise;
  return res.data as T;
};

export interface DashboardWidget {
  id: string;
  type: 'kpi' | 'bar' | 'line' | 'pie' | 'area' | 'table';
  title: string;
  data: any;
  config?: any;
}

export interface DashboardFragment {
  widgets: DashboardWidget[];
  layout: string;
  description: string;
}

export interface HealthCheckResponse {
  status: string;
  dataset_loaded: boolean;
  rules_loaded: number;
  scored_count: number;
}

export const apiService = {
  uploadDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      return asJson<UploadResponse>(
        api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      );
    } catch (err: any) {
      if (err.response && err.response.data?.detail) {
        // Erreur renvoyée par l'API backend
        throw new Error('Erreur API : ' + err.response.data.detail);
      } else if (err.response && err.response.data) {
        // Erreur structurée renvoyée mais sans champ .detail
        throw new Error('Erreur API : ' + JSON.stringify(err.response.data));
      } else if (err.request) {
        // Pas de réponse du tout (timeout, backend down)
        throw new Error("Erreur réseau : le backend n'a pas répondu.");
      } else {
        // Erreur technique JS/axios
        throw new Error('Erreur technique : ' + err.message);
      }
    }
  },
  getDatasetPreview: async (fileId: string) =>
    asJson<UploadResponse>(api.get('/dataset', { params: { file_id: fileId } })),
  analyzeDataset: async (fileId: string) =>
    asJson<AnalyzeResponse>(api.post('/analyze', { file_id: fileId })),
  getPlots: async (fileId: string) => asJson<PlotResponse>(api.post('/plots', { file_id: fileId })),
  getFeatures: async (fileId: string) => asJson<FeatureResponse>(api.post('/features', { file_id: fileId })),
  getRules: async (fileId: string) => asJson<RuleResponse>(api.post('/rules', { file_id: fileId })),
  getRecommendations: async (fileId: string) =>
    asJson<RecommendationResponse>(api.post('/recommendations', { file_id: fileId })),
  healthCheck: async () => asJson<HealthCheckResponse>(api.get('/health')),
  generateDashboardFragment: async () => 
    asJson<DashboardFragment>(api.post('/dashboard/generate-fragment')),
};

export default apiService;


