import axios from 'axios';
import type { 
  DocumentItem, 
  TransactionItem, 
  ReconciliationSummaryReport, 
  ClassifierMetricsResponse,
  ReconciliationMode,
  DashboardStatsResponse,
  DiscrepancyItem,
  EvidenceItem,
  ComparisonResult,
  ReconciliationRunItem,
  TransactionGraph,
  BenchmarkEvaluationReport,
  AblationStudyReport,
  DisputeNoticeResponse
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

  reclassifyDocument: async (docId: string, targetType: string): Promise<DocumentItem> => {
    const res = await axios.post<DocumentItem>(`${API_BASE}/documents/${docId}/reclassify?target_type=${targetType}`);
    return res.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE}/documents/${id}`);
  },

  seedDemo: async (): Promise<DocumentItem[]> => {
    const res = await axios.post<DocumentItem[]>(`${API_BASE}/documents/upload`);
    return res.data;
  },

  deleteTransaction: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE}/transactions/${id}`);
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

  getTransactionGraph: async (id: string): Promise<TransactionGraph> => {
    const res = await axios.get<TransactionGraph>(`${API_BASE}/transactions/${id}/graph`);
    return res.data;
  },

  confirmDocumentLink: async (txnId: string, linkId: string): Promise<void> => {
    await axios.post(`${API_BASE}/transactions/${txnId}/links/${linkId}/confirm`);
  },

  removeDocumentLink: async (txnId: string, linkId: string): Promise<void> => {
    await axios.delete(`${API_BASE}/transactions/${txnId}/links/${linkId}`);
  },

  cleanupEmptyTransactions: async (): Promise<void> => {
    await axios.delete(`${API_BASE}/transactions/cleanup-empty`);
  },

  getDisputeNotice: async (txnId: string): Promise<DisputeNoticeResponse> => {
    const res = await axios.get<DisputeNoticeResponse>(`${API_BASE}/transactions/${txnId}/dispute-notice`);
    return res.data;
  },

  // 3. Three-Way Reconciliation Engines API
  compareApproaches: async (transactionId: string): Promise<ComparisonResult> => {
    const res = await axios.post<ComparisonResult>(`${API_BASE}/reconciliation/compare`, {
      transaction_id: transactionId,
      approach: 'HYBRID'
    });
    return res.data;
  },

  runRuleBased: async (transactionId: string): Promise<ReconciliationRunItem> => {
    const res = await axios.post<ReconciliationRunItem>(`${API_BASE}/reconciliation/rule`, {
      transaction_id: transactionId,
      approach: 'RULE_BASED'
    });
    return res.data;
  },

  runAILlm: async (transactionId: string): Promise<ReconciliationRunItem> => {
    const res = await axios.post<ReconciliationRunItem>(`${API_BASE}/reconciliation/ai`, {
      transaction_id: transactionId,
      approach: 'AI_LLM'
    });
    return res.data;
  },

  runHybrid: async (transactionId: string): Promise<ReconciliationRunItem> => {
    const res = await axios.post<ReconciliationRunItem>(`${API_BASE}/reconciliation/hybrid`, {
      transaction_id: transactionId,
      approach: 'HYBRID'
    });
    return res.data;
  },

  // Backward-compatible run
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

  // 4. Research Benchmark & Evaluation API
  runBenchmark: async (): Promise<BenchmarkEvaluationReport> => {
    const res = await axios.post<BenchmarkEvaluationReport>(`${API_BASE}/evaluation/run`);
    return res.data;
  },

  getBenchmarkResults: async (): Promise<BenchmarkEvaluationReport> => {
    const res = await axios.get<BenchmarkEvaluationReport>(`${API_BASE}/evaluation/results`);
    return res.data;
  },

  getGroundTruthDataset: async (): Promise<any> => {
    const res = await axios.get(`${API_BASE}/evaluation/ground-truth`);
    return res.data;
  },

  exportResearchReport: async (): Promise<string> => {
    const res = await axios.get<string>(`${API_BASE}/evaluation/export-report`, {
      responseType: 'text'
    });
    return res.data;
  },

  getClassifierMetrics: async (): Promise<ClassifierMetricsResponse> => {
    const res = await axios.get<ClassifierMetricsResponse>(`${API_BASE}/evaluation/classifier-metrics`);
    return res.data;
  },

  getAblationStudy: async (): Promise<AblationStudyReport> => {
    const res = await axios.get<AblationStudyReport>(`${API_BASE}/evaluation/ablation`);
    return res.data;
  },

  // 5. Dashboard Stats API
  getDashboardStats: async (): Promise<DashboardStatsResponse> => {
    const res = await axios.get<DashboardStatsResponse>(`${API_BASE}/dashboard/stats`);
    return res.data;
  },

  // 6. Evidence API
  getEvidence: async (id: string): Promise<EvidenceItem> => {
    const res = await axios.get<EvidenceItem>(`${API_BASE}/evidence/${id}`);
    return res.data;
  }
};
