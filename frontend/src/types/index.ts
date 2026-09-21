export type DocumentType = 
  | 'PURCHASE_ORDER'
  | 'INVOICE'
  | 'DELIVERY_NOTE'
  | 'PAYMENT_RECEIPT'
  | 'QUOTATION'
  | 'CREDIT_NOTE'
  | 'DEBIT_NOTE'
  | 'UNKNOWN';

export type ProcessStatus = 
  | 'UPLOADED' 
  | 'PROCESSING' 
  | 'EXTRACTED' 
  | 'CLASSIFIED' 
  | 'MATCHED' 
  | 'RECONCILED' 
  | 'FAILED';

export type WorkflowStep = 'UPLOAD' | 'EXTRACT' | 'CLASSIFY' | 'MATCH' | 'RECONCILE' | 'RESULTS';

export interface WorkflowFileItem {
  id: string;
  file: File;
  filename: string;
  size: number;
  documentType?: DocumentType | string;
  classificationConfidence?: number;
  uploadStatus: 'IDLE' | 'PROCESSING' | 'UPLOADED' | 'FAILED';
  extractionStatus: 'IDLE' | 'PROCESSING' | 'EXTRACTED' | 'FAILED';
  classificationStatus: 'IDLE' | 'PROCESSING' | 'CLASSIFIED' | 'FAILED';
  matchStatus: 'IDLE' | 'PROCESSING' | 'MATCHED' | 'FAILED';
  reconcileStatus: 'IDLE' | 'PROCESSING' | 'RECONCILED' | 'FAILED';
  overallStatus: ProcessStatus | 'IDLE';
  errorMessage?: string | null;
  extractedPageCount?: number;
  extractedItemCount?: number;
  rawTextPreview?: string;
  backendDocId?: string;
  transactionId?: string;
}

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ReconciliationMode = 'RULE_BASED' | 'AI_ONLY' | 'HYBRID';
export type TransactionStatus = 'RECONCILED' | 'DISCREPANCY_FOUND' | 'INCOMPLETE' | 'PENDING' | 'MINOR_VARIANCE';

export interface LineItem {
  item_id?: string;
  description: string;
  normalized_description?: string;
  quantity: string | number;
  unit: string;
  unit_price: string | number;
  discount?: string | number;
  tax_rate?: string | number;
  tax_amount?: string | number;
  total_amount: string | number;
  evidence_snippet?: string;
  page_number?: number;
}

export interface ParsedDocumentData {
  document_number?: string;
  po_reference?: string;
  invoice_reference?: string;
  document_date?: string;
  due_date?: string;
  supplier_name?: string;
  supplier_gstin?: string;
  customer_name?: string;
  customer_gstin?: string;
  delivery_address?: string;
  items?: LineItem[];
  subtotal?: string | number;
  tax_total?: string | number;
  grand_total?: string | number;
  payment_amount?: string | number;
  payment_method?: string;
  transaction_reference?: string;
  adjustment_amount?: string | number;
  reason_for_adjustment?: string;
  prob_dist?: Record<string, number>;
  extra_metadata?: Record<string, any>;
}

export interface DocumentItem {
  id: string;
  original_pdf_id?: string;
  page_number?: number;
  filename: string;
  file_type: string;
  doc_type: DocumentType;
  document_type?: DocumentType;
  classification_confidence: number;
  confidence?: number;
  page_count: number;
  raw_text: string;
  extracted_text?: string;
  parsed_data: ParsedDocumentData;
  status: string;
  created_at: string;
}

export interface EvidenceItem {
  id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  field_name: string;
  exact_value: string;
  snippet: string;
  relevance_score: number;
  created_at: string;
}

export interface DiscrepancyItem {
  id: string;
  transaction_id: string;
  rule_code: string;
  discrepancy_type: string;
  severity: SeverityLevel;
  confidence: number;
  title: string;
  description: string;
  difference_amount: number;
  expected_value?: string;
  actual_value?: string;
  difference_value?: string;
  llm_explanation: string;
  status: string;
  created_at: string;
  evidences: EvidenceItem[];
}

export interface TransactionItem {
  id: string;
  transaction_ref: string;
  title: string;
  supplier_name: string;
  customer_name: string;
  total_amount: number;
  reconciliation_status: TransactionStatus;
  reconciliation_summary: string;
  created_at: string;
  updated_at: string;
  documents: DocumentItem[];
  discrepancies: DiscrepancyItem[];
}

export interface ReconciliationSummaryReport {
  transaction_id: string;
  transaction_ref: string;
  reconciliation_status: TransactionStatus;
  mode_used: ReconciliationMode;
  total_documents: number;
  documents_summary: Array<{ filename: string; doc_type: string; status: string }>;
  total_discrepancies: number;
  discrepancies_by_severity: Record<SeverityLevel, number>;
  discrepancies: DiscrepancyItem[];
  financial_variance_amount: number;
  ai_grounded_explanation: string;
  generated_at: string;
}

export interface ModeBenchmarkMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  reconciliation_accuracy: number;
  evidence_accuracy: number;
  avg_latency_ms: number;
  cases: Array<{
    case_id: string;
    title: string;
    expected: string[];
    predicted: string[];
    precision: number;
    recall: number;
    f1: number;
  }>;
}

export interface BenchmarkResponse {
  evaluated_at: string;
  total_test_cases: number;
  modes: Record<ReconciliationMode, ModeBenchmarkMetrics>;
}

export interface ClassifierMetricsResponse {
  accuracy: number;
  labels: string[];
  classification_report: Record<string, any>;
  confusion_matrix: number[][];
  train_samples: number;
  test_samples: number;
}

export interface DashboardStatsResponse {
  total_transactions: number;
  reconciled_transactions: number;
  discrepancy_transactions: number;
  needs_review_transactions: number;
  total_documents: number;
  total_outstanding_amount: number;
  total_invoiced_amount: number;
  total_discrepancies: number;
  discrepancies_by_type: Record<string, number>;
  discrepancies_by_severity: Record<string, number>;
  status_distribution: Record<string, number>;
}

