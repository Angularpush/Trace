import axios from 'axios';
import type { 
  DocumentItem, 
  TransactionItem, 
  ReconciliationSummaryReport, 
  BenchmarkResponse, 
  ClassifierMetricsResponse,
  ReconciliationMode,
  DashboardStatsResponse,
  DiscrepancyItem,
  EvidenceItem
} from '../types';

const rawBase = (import.meta.env.VITE_API_URL as string) || '';
const API_BASE = rawBase ? `${rawBase.replace(/\/$/, '')}/api` : '/api';

export const api = {
  // 1. Documents API
  uploadDocuments: async (files: File[], docType?: string): Promise<DocumentItem[]> => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    if (docType) {
      formData.append('doc_type', docType);
    }
    const res = await axios.post<DocumentItem[]>(`${API_BASE}/documents/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  listDocuments: async (): Promise<DocumentItem[]> => {
    const res = await axios.get<DocumentItem[]>(`${API_BASE}/documents/`);
    return res.data;
  },

  getDocument: async (id: string): Promise<DocumentItem> => {
    const res = await axios.get<DocumentItem>(`${API_BASE}/documents/${id}`);
    return res.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE}/documents/${id}`);
  },

  seedDemo: async (): Promise<DocumentItem[]> => {
    const res = await axios.post<DocumentItem[]>(`${API_BASE}/documents/seed-demo`);
    return res.data;
  },

  // 2. Transactions API
  matchTransactions: async (): Promise<TransactionItem[]> => {
    const res = await axios.post<TransactionItem[]>(`${API_BASE}/transactions/match`);
    return res.data;
  },

  autoLinkTransactions: async (): Promise<TransactionItem[]> => {
    const res = await axios.post<TransactionItem[]>(`${API_BASE}/transactions/match`);
    return res.data;
  },

  listTransactions: async (): Promise<TransactionItem[]> => {
    const res = await axios.get<TransactionItem[]>(`${API_BASE}/transactions/`);
    return res.data;
  },

  getTransaction: async (id: string): Promise<TransactionItem> => {
    const res = await axios.get<TransactionItem>(`${API_BASE}/transactions/${id}`);
    return res.data;
  },

  reconcileTransaction: async (
    id: string,
    mode: ReconciliationMode = 'HYBRID',
    llmProvider: string = 'offline'
  ): Promise<ReconciliationSummaryReport> => {
    const res = await axios.post<ReconciliationSummaryReport>(
      `${API_BASE}/transactions/${id}/reconcile?mode=${mode}&llm_provider=${llmProvider}`
    );
    return res.data;
  },

  runReconciliation: async (
    transactionId: string, 
    mode: ReconciliationMode = 'HYBRID',
    llmProvider: string = 'offline'
  ): Promise<ReconciliationSummaryReport> => {
    const res = await axios.post<ReconciliationSummaryReport>(
      `${API_BASE}/transactions/${transactionId}/reconcile?mode=${mode}&llm_provider=${llmProvider}`
    );
    return res.data;
  },

  getTransactionReport: async (id: string): Promise<ReconciliationSummaryReport> => {
    const res = await axios.get<ReconciliationSummaryReport>(`${API_BASE}/transactions/${id}/report`);
    return res.data;
  },

  getReconciliationReport: async (transactionId: string): Promise<ReconciliationSummaryReport> => {
    const res = await axios.get<ReconciliationSummaryReport>(`${API_BASE}/transactions/${transactionId}/report`);
    return res.data;
  },

  getTransactionDiscrepancies: async (id: string): Promise<DiscrepancyItem[]> => {
    const res = await axios.get<DiscrepancyItem[]>(`${API_BASE}/transactions/${id}/discrepancies`);
    return res.data;
  },

  // 3. Evidence API
  getEvidence: async (id: string): Promise<EvidenceItem> => {
    const res = await axios.get<EvidenceItem>(`${API_BASE}/evidence/${id}`);
    return res.data;
  },

  // 4. Evaluation API
  runEvaluation: async (): Promise<BenchmarkResponse> => {
    const res = await axios.post<BenchmarkResponse>(`${API_BASE}/evaluation/run`);
    return res.data;
  },

  getEvaluationResults: async (): Promise<BenchmarkResponse | null> => {
    const res = await axios.get<BenchmarkResponse | null>(`${API_BASE}/evaluation/results`);
    return res.data;
  },

  getLatestEvaluation: async (): Promise<BenchmarkResponse | null> => {
    const res = await axios.get<BenchmarkResponse | null>(`${API_BASE}/evaluation/latest`);
    return res.data;
  },

  getBenchmark: async (): Promise<BenchmarkResponse> => {
    const res = await axios.get<BenchmarkResponse>(`${API_BASE}/evaluation/benchmark`);
    return res.data;
  },

  getClassifierMetrics: async (): Promise<ClassifierMetricsResponse> => {
    const res = await axios.get<ClassifierMetricsResponse>(`${API_BASE}/evaluation/classifier-metrics`);
    return res.data;
  },

  // 5. Dashboard API
  getDashboardStats: async (): Promise<DashboardStatsResponse> => {
    const res = await axios.get<DashboardStatsResponse>(`${API_BASE}/dashboard/stats`);
    return res.data;
  }
};
