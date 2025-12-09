/** API service for communicating with the backend. */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API key (if needed)
api.interceptors.request.use((config) => {
  const apiKey = import.meta.env.VITE_API_KEY;
  if (apiKey) {
    config.headers['X-API-KEY'] = apiKey;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    // Extract detailed error message from backend
    if (error.response?.data?.detail) {
      error.message = error.response.data.detail;
    } else if (error.response?.data?.message) {
      error.message = error.response.data.message;
    }
    return Promise.reject(error);
  }
);

export interface CustomerScore {
  customer_id: string;
  priority_score: number;
  priority_label: 'high' | 'medium' | 'low';
  rules_fired: RuleFired[];
  explain: Record<string, any>;
  raw_data: Record<string, any>;
}

export interface RuleFired {
  rule_id: string;
  rule_label: string;
  points: number;
  reason: string;
}

export interface RuleConfig {
  id: string;
  label: string;
  condition: string;
  points: number;
  description: string;
  enabled: boolean;
  threshold?: number;
}

export interface ScoreResponse {
  results: CustomerScore[];
  total_scored: number;
  summary: {
    high: number;
    medium: number;
    low: number;
    total: number;
  };
}

export interface RecommendationResponse {
  customers: CustomerScore[];
  total_count: number;
  metadata: {
    high_count: number;
    medium_count: number;
    low_count: number;
    avg_score: number;
  };
}

export interface CustomerDetailResponse {
  customer: CustomerScore;
  suggested_action: string;
}

export interface CampaignSimulationResponse {
  estimated_conversion_rate: number;
  estimated_revenue: number;
  total_customers: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  kpis: Record<string, any>;
}

export interface ColumnStatisticsResponse {
  columns: string[];
  numeric_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  column_stats: Record<string, any>;
  available_charts: string[];
}

export interface AIAnalysisResponse {
  analysis: Record<string, any>;
  recommendations: Record<string, any>;
  transformation_plan: Record<string, any>;
  suggested_charts: Array<{
    type: string;
    reason: string;
    columns: string[];
    priority: string;
  }>;
  feature_engineering_suggestions: Array<{
    type: string;
    formula: string;
    reason: string;
  }>;
  ai_enabled: boolean;
}

// API functions
export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // Upload dataset
  uploadDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Score customers
  scoreCustomers: async (data: Record<string, any>[]) => {
    const response = await api.post<ScoreResponse>('/score', { data });
    return response.data;
  },

  // Score uploaded dataset
  scoreUploadedDataset: async () => {
    const response = await api.post<ScoreResponse>('/score/upload');
    return response.data;
  },

  // Get recommendations
  getRecommendations: async (topN: number = 50, priorityLabel?: string, minScore?: number) => {
    const params: Record<string, any> = { top_n: topN };
    if (priorityLabel) params.priority_label = priorityLabel;
    if (minScore !== undefined) params.min_score = minScore;
    
    const response = await api.get<RecommendationResponse>('/recommendations', { params });
    return response.data;
  },

  // Get customer detail
  getCustomerDetail: async (customerId: string) => {
    const response = await api.get<CustomerDetailResponse>(`/customer/${customerId}`);
    return response.data;
  },

  // Get rules
  getRules: async () => {
    const response = await api.get<{ rules: RuleConfig[] }>('/rules');
    return response.data;
  },

  // Update rule
  updateRule: async (ruleId: string, updates: { enabled?: boolean; threshold?: number; points?: number }) => {
    const response = await api.put(`/rules/${ruleId}`, updates, {
      headers: {
        'X-API-KEY': import.meta.env.VITE_API_KEY || 'demo-api-key-change-in-production',
      },
    });
    return response.data;
  },

  // Simulate campaign
  simulateCampaign: async (topN: number = 50) => {
    const response = await api.post<CampaignSimulationResponse>('/simulate_campaign', { top_n: topN });
    return response.data;
  },

  // Get dataset statistics
  getDatasetStatistics: async () => {
    const response = await api.get<ColumnStatisticsResponse>('/datasets/latest/statistics');
    return response.data;
  },

  // Get AI analysis and recommendations
  getAIAnalysis: async () => {
    const response = await api.get<AIAnalysisResponse>('/datasets/latest/ai-analysis');
    return response.data;
  },
};

export default api;


