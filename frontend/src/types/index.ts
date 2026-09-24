export type DocumentType = 
  | 'PURCHASE_ORDER'
  | 'INVOICE'
  | 'DELIVERY_NOTE'
  | 'PAYMENT_RECEIPT'
  | 'QUOTATION'
  | 'CREDIT_NOTE'
  | 'DEBIT_NOTE'
  | 'BANK_STATEMENT'
  | 'OTHER'
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
export type ReconciliationMode = 'RULE_BASED' | 'AI_ONLY' | 'AI_LLM' | 'HYBRID';
export type ReconciliationApproach = 'RULE_BASED' | 'AI_LLM' | 'HYBRID';
export type TransactionStatus = 'RECONCILED' | 'DISCREPANCY_FOUND' | 'DISCREPANCIES_FOUND' | 'INCOMPLETE' | 'PENDING' | 'MINOR_VARIANCE';

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
  file_id?: string;
  original_pdf_id?: string;
  page_number?: number;
  page_start?: number;
  page_end?: number;
  filename: string;
  file_type: string;
  doc_type: DocumentType;
  document_type?: DocumentType;
  classification_confidence: number;
  confidence?: number;
  classification_method?: string;
  page_count: number;
  raw_text: string;
  extracted_text?: string;
  parsed_data: ParsedDocumentData;
  structured_data?: ParsedDocumentData;
  status: string;
  created_at: string;
}

export interface EvidenceItem {
  id?: string;
  document_id?: string;
  document_name?: string;
  page_number?: number;
  field_name?: string;
  exact_value?: string;
  snippet: string;
  relevance_score?: number;
  created_at?: string;
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

export interface TransactionDocumentLink {
  id?: string;
  transaction_id: string;
  document_id: string;
  link_method: string;
  link_confidence: number;
  confirmed: boolean;
  link_details?: Record<string, any>;
  created_at?: string;
  document?: DocumentItem;
}

export interface TransactionItem {
  id: string;
  transaction_reference?: string;
  transaction_ref: string;
  title: string;
  supplier?: string;
  customer?: string;
  supplier_name: string;
  customer_name: string;
  total_amount: number;
  currency?: string;
  status?: string;
  reconciliation_status: TransactionStatus;
  reconciliation_summary: string;
  created_at: string;
  updated_at: string;
  documents: DocumentItem[];
  document_links?: TransactionDocumentLink[];
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

export interface EngineFindingItem {
  id?: string;
  discrepancy_type: string;
  severity: SeverityLevel;
  expected_value: string;
  actual_value: string;
  difference_value: string;
  explanation: string;
  confidence: number;
  evidence: EvidenceItem[];
  source_documents: string[];
  provenance: 'rule' | 'semantic' | 'llm';
  title?: string;
}

export interface ReconciliationRunItem {
  id: string;
  transaction_id?: string;
  approach: ReconciliationApproach;
  overall_result: string;
  execution_time_ms: number;
  cost_usd: number;
  findings_count: number;
  findings: EngineFindingItem[];
  summary_text?: string;
  model_version?: string;
}

export interface ComparisonResult {
  transaction_id: string;
  transaction_reference: string;
  rule_based_run?: ReconciliationRunItem;
  ai_llm_run?: ReconciliationRunItem;
  hybrid_run?: ReconciliationRunItem;
  agreement_score: number;
  consensus_discrepancies: string[];
  conflicting_discrepancies: string[];
  latency_comparison: Record<string, number>;
  cost_comparison: Record<string, number>;
  explanation_summary: string;
}

export interface TransactionGraphNode {
  id: string;
  document_type: string;
  document_number: string;
  filename: string;
  page_start: number;
  page_end: number;
  total_amount: number;
  date?: string;
}

export interface TransactionGraphEdge {
  id?: string;
  transaction_id?: string;
  document_id?: string;
  from_doc_id?: string;
  to_doc_id?: string;
  link_method: string;
  link_confidence: number;
  confirmed: boolean;
  link_details?: Record<string, any>;
}

export interface TransactionGraph {
  transaction_id: string;
  transaction_reference: string;
  nodes: TransactionGraphNode[];
  edges: TransactionGraphEdge[];
}

export interface DiscrepancyMetricDetail {
  discrepancy_type: string;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface ApproachEvaluationSummary {
  approach: string;
  total_evaluated_transactions: number;
  precision: number;
  recall: number;
  f1_score: number;
  linking_accuracy: number;
  evidence_accuracy: number;
  avg_execution_time_ms: number;
  total_cost_usd: number;
  cost_per_transaction_usd: number;
  category_breakdown: DiscrepancyMetricDetail[];
}

export interface BenchmarkEvaluationReport {
  benchmark_id: string;
  run_timestamp: string;
  dataset_size: number;
  categories_tested: number;
  rule_based_metrics: ApproachEvaluationSummary;
  ai_llm_metrics: ApproachEvaluationSummary;
  hybrid_metrics: ApproachEvaluationSummary;
  key_findings: string[];
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
  benchmark_summary?: BenchmarkEvaluationReport;
}

export interface AblationConfigItem {
  config_id: string;
  name: string;
  components: string;
  precision: number;
  recall: number;
  f1_score: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  evidence_accuracy: number;
  key_characteristic: string;
}

export interface AblationStudyReport {
  dataset_size: number;
  timestamp: string;
  configurations: AblationConfigItem[];
  insights: string[];
}

export interface DisputeDiscrepancyRow {
  title: string;
  discrepancy_type: string;
  severity: string;
  expected_value: string;
  actual_value: string;
  variance_amount: string;
  explanation: string;
  statutory_rule: string;
}

export interface DisputeNoticeResponse {
  dispute_reference: string;
  transaction_id: string;
  transaction_reference: string;
  audit_date: string;
  supplier_name: string;
  customer_name: string;
  total_discrepancies: number;
  total_variance_amount: number;
  discrepancies: DisputeDiscrepancyRow[];
  formal_letter_markdown: string;
}
