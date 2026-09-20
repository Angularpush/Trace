import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Image as ImageIcon,
  X, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowRight, 
  RotateCw, 
  Cpu, 
  Layers, 
  CheckCheck,
  ChevronRight,
  FileCheck2,
  ListOrdered
} from 'lucide-react';
import { api } from '../../api';
import type { 
  DocumentItem, 
  WorkflowFileItem, 
  WorkflowStep, 
  TransactionItem 
} from '../../types';
import { DocTypeBadge, ProcessStatusBadge, SeverityBadge, StatusBadge } from '../common/Badge';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (docs: DocumentItem[]) => void;
  onNavigateToTransaction?: (txnId: string) => void;
}

const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg'];
const ALLOWED_MIME_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const isAllowedFile = (file: File): boolean => {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  return ALLOWED_EXTENSIONS.includes(ext) || ALLOWED_MIME_TYPES.includes(file.type);
};

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({ 
  isOpen, 
  onClose, 
  onUploadSuccess,
  onNavigateToTransaction 
}) => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('UPLOAD');
  const [fileItems, setFileItems] = useState<WorkflowFileItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  
  // Results state
  const [createdTransactions, setCreatedTransactions] = useState<TransactionItem[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFilesSelected = (files: FileList | null) => {
    if (!files) return;
    setGlobalError(null);

    const newItems: WorkflowFileItem[] = Array.from(files).map((file) => {
      const valid = isAllowedFile(file);
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      
      return {
        id: `file_${Math.random().toString(36).substring(2, 9)}`,
        file,
        filename: file.name,
        size: file.size,
        uploadStatus: valid ? 'IDLE' : 'FAILED',
        extractionStatus: 'IDLE',
        classificationStatus: 'IDLE',
        matchStatus: 'IDLE',
        reconcileStatus: 'IDLE',
        overallStatus: valid ? 'IDLE' : 'FAILED',
        errorMessage: valid ? null : `Unsupported file format '${ext}'. Allowed: PDF, PNG, JPG, JPEG.`
      };
    });

    setFileItems((prev) => [...prev, ...newItems]);
  };

  const handleRemoveFile = (id: string) => {
    setFileItems((prev) => prev.filter((item) => item.id !== id));
  };

  const handleClearAll = () => {
    setFileItems([]);
    setGlobalError(null);
    setCurrentStep('UPLOAD');
    setCreatedTransactions([]);
  };

  // Run the complete real backend workflow
  const handleStartWorkflow = async () => {
    const validItems = fileItems.filter((item) => item.overallStatus !== 'FAILED');
    if (validItems.length === 0) {
      setGlobalError('Please select at least one valid PDF, PNG, JPG, or JPEG file.');
      return;
    }

    setIsProcessing(true);
    setGlobalError(null);

    try {
      // -------------------------------------------------------------
      // STAGE 1: UPLOAD, EXTRACT & CLASSIFY
      // -------------------------------------------------------------
      setCurrentStep('UPLOAD');
      setFileItems((prev) =>
        prev.map((item) =>
          item.overallStatus !== 'FAILED'
            ? {
                ...item,
                uploadStatus: 'PROCESSING',
                extractionStatus: 'PROCESSING',
                classificationStatus: 'PROCESSING',
                overallStatus: 'PROCESSING',
                errorMessage: null
              }
            : item
        )
      );

      const filesToUpload = validItems.map((item) => item.file);
      let uploadedDocs: DocumentItem[] = [];

      try {
        uploadedDocs = await api.uploadDocuments(filesToUpload);

        // Update items with extraction & classification results
        setFileItems((prev) =>
          prev.map((item) => {
            const matchedDoc = uploadedDocs.find(
              (d) => d.filename === item.filename || d.filename.endsWith(item.filename)
            );
            if (matchedDoc) {
              return {
                ...item,
                backendDocId: matchedDoc.id,
                documentType: matchedDoc.doc_type,
                classificationConfidence: matchedDoc.classification_confidence,
                extractedPageCount: matchedDoc.page_count,
                extractedItemCount: matchedDoc.parsed_data?.items?.length || 0,
                rawTextPreview: matchedDoc.raw_text,
                uploadStatus: 'UPLOADED',
                extractionStatus: 'EXTRACTED',
                classificationStatus: 'CLASSIFIED',
                overallStatus: 'CLASSIFIED'
              };
            }
            return item;
          })
        );
      } catch (uploadErr: any) {
        const errorDetail = uploadErr?.response?.data?.detail || uploadErr?.message || 'Upload & Extraction failed on backend.';
        setGlobalError(errorDetail);
        setFileItems((prev) =>
          prev.map((item) =>
            item.overallStatus === 'PROCESSING'
              ? {
                  ...item,
                  uploadStatus: 'FAILED',
                  extractionStatus: 'FAILED',
                  classificationStatus: 'FAILED',
                  overallStatus: 'FAILED',
                  errorMessage: errorDetail
                }
              : item
          )
        );
        setIsProcessing(false);
        return; // Halt workflow on backend failure
      }

      // -------------------------------------------------------------
      // STAGE 2: MATCH (TRANSACTION LINKING)
      // -------------------------------------------------------------
      setCurrentStep('MATCH');
      setFileItems((prev) =>
        prev.map((item) =>
          item.overallStatus === 'CLASSIFIED'
            ? { ...item, matchStatus: 'PROCESSING', overallStatus: 'PROCESSING' }
            : item
        )
      );

      let linkedTxns: TransactionItem[] = [];
      try {
        linkedTxns = await api.autoLinkTransactions();
        setCreatedTransactions(linkedTxns);

        setFileItems((prev) =>
          prev.map((item) => {
            if (item.backendDocId) {
              const matchedTxn = linkedTxns.find((txn) =>
                txn.documents.some((d) => d.id === item.backendDocId)
              );
              return {
                ...item,
                matchStatus: 'MATCHED',
                overallStatus: 'MATCHED',
                transactionId: matchedTxn?.id
              };
            }
            return item;
          })
        );
      } catch (matchErr: any) {
        const errorDetail = matchErr?.response?.data?.detail || matchErr?.message || 'Transaction linking failed on backend.';
        setGlobalError(errorDetail);
        setFileItems((prev) =>
          prev.map((item) =>
            item.overallStatus === 'PROCESSING'
              ? { ...item, matchStatus: 'FAILED', overallStatus: 'FAILED', errorMessage: errorDetail }
              : item
          )
        );
        setIsProcessing(false);
        return;
      }

      // -------------------------------------------------------------
      // STAGE 3: RECONCILE (DETERMINISTIC FINANCIAL RULES & AUDIT)
      // -------------------------------------------------------------
      setCurrentStep('RECONCILE');
      setFileItems((prev) =>
        prev.map((item) =>
          item.overallStatus === 'MATCHED'
            ? { ...item, reconcileStatus: 'PROCESSING', overallStatus: 'PROCESSING' }
            : item
        )
      );

      // Reconcile each discovered transaction
      for (const txn of linkedTxns) {
        try {
          await api.runReconciliation(txn.id, 'HYBRID', 'offline');
        } catch (reconErr: any) {
          console.warn(`Reconciliation failed for transaction ${txn.id}:`, reconErr);
        }
      }

      // Refresh transactions to get latest discrepancy items
      const refreshedTxns = await api.listTransactions();
      setCreatedTransactions(refreshedTxns);

      setFileItems((prev) =>
        prev.map((item) => {
          if (item.overallStatus === 'PROCESSING' || item.overallStatus === 'MATCHED') {
            return {
              ...item,
              reconcileStatus: 'RECONCILED',
              overallStatus: 'RECONCILED'
            };
          }
          return item;
        })
      );

      // -------------------------------------------------------------
      // STAGE 4: RESULTS
      // -------------------------------------------------------------
      setCurrentStep('RESULTS');
      onUploadSuccess(uploadedDocs);

    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'An unexpected error occurred during processing.';
      setGlobalError(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const stepsList: Array<{ id: WorkflowStep; label: string; icon: any }> = [
    { id: 'UPLOAD', label: 'Upload', icon: UploadCloud },
    { id: 'EXTRACT', label: 'Extract', icon: FileText },
    { id: 'CLASSIFY', label: 'Classify', icon: Cpu },
    { id: 'MATCH', label: 'Match', icon: Layers },
    { id: 'RECONCILE', label: 'Reconcile', icon: CheckCheck },
    { id: 'RESULTS', label: 'Results', icon: FileCheck2 },
  ];

  const getStepIndex = (step: WorkflowStep): number => {
    return stepsList.findIndex((s) => s.id === step);
  };

  const currentStepIdx = getStepIndex(currentStep);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200 my-8">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-slate-950/60">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
              <h2 className="text-lg font-bold text-slate-100">TRACE Document Ingestion & Reconciliation</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              End-to-End Pipeline: Upload &bull; PyMuPDF Extraction &bull; Supervised ML Classification &bull; Graph Matching &bull; Financial Audit
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Workflow Stepper Bar */}
        <div className="px-6 py-4 bg-slate-950/40 border-b border-slate-800">
          <div className="flex items-center justify-between relative">
            {/* Connecting line */}
            <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-0.5 bg-slate-800 -z-0" />
            
            {stepsList.map((st, idx) => {
              const isPast = idx < currentStepIdx;
              const isCurrent = idx === currentStepIdx;
              const Icon = st.icon;

              return (
                <div key={st.id} className="relative z-10 flex flex-col items-center">
                  <div 
                    className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all ${
                      isCurrent
                        ? 'bg-indigo-600 border-indigo-400 text-white shadow-lg shadow-indigo-600/40 scale-110'
                        : isPast
                        ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400'
                        : 'bg-slate-900 border-slate-800 text-slate-500'
                    }`}
                  >
                    {isProcessing && isCurrent ? (
                      <Loader2 className="w-4 h-4 animate-spin text-white" />
                    ) : isPast ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>
                  <span 
                    className={`text-[11px] font-bold mt-1.5 transition-colors ${
                      isCurrent
                        ? 'text-indigo-400'
                        : isPast
                        ? 'text-emerald-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {st.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[68vh] overflow-y-auto">

          {/* Global Alert Banner */}
          {globalError && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-bold text-rose-200">Backend Processing Error</p>
                <p className="font-mono text-[11px] whitespace-pre-wrap">{globalError}</p>
              </div>
            </div>
          )}

          {/* VIEW: RESULTS STAGE */}
          {currentStep === 'RESULTS' ? (
            <div className="space-y-6 animate-in fade-in duration-300">
              
              {/* Success Banner */}
              <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <CheckCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Reconciliation Pipeline Completed</h3>
                    <p className="text-xs text-slate-400">
                      Processed {fileItems.length} documents &bull; Discovered {createdTransactions.length} transaction clusters
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleClearAll}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                  <span>Upload Another Batch</span>
                </button>
              </div>

              {/* Transactions Discovered */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span>Linked Transactions & Audit Status</span>
                </h4>

                {createdTransactions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {createdTransactions.map((txn) => {
                      const discCount = txn.discrepancies?.length || 0;
                      const hasDiscrepancy = discCount > 0;

                      return (
                        <div 
                          key={txn.id}
                          className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition space-y-3"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <span className="font-mono text-xs font-bold text-indigo-400">{txn.transaction_ref}</span>
                              <h5 className="font-semibold text-xs text-slate-200 mt-0.5">{txn.title || 'MSME Transaction'}</h5>
                            </div>
                            <StatusBadge status={txn.reconciliation_status} />
                          </div>

                          <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2">
                            <span><b>Docs:</b> {txn.documents?.length || 0} files</span>
                            <span className={hasDiscrepancy ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {discCount} Discrepanc{discCount === 1 ? 'y' : 'ies'}
                            </span>
                          </div>

                          {/* Quick Discrepancy Preview */}
                          {hasDiscrepancy && (
                            <div className="space-y-1.5 bg-rose-950/10 p-2.5 rounded-xl border border-rose-500/20">
                              {txn.discrepancies.slice(0, 2).map((d) => (
                                <div key={d.id} className="flex items-center justify-between text-[10px]">
                                  <span className="text-slate-300 font-medium truncate max-w-[200px]">{d.title}</span>
                                  <SeverityBadge severity={d.severity} />
                                </div>
                              ))}
                              {txn.discrepancies.length > 2 && (
                                <p className="text-[10px] text-slate-500 italic">
                                  +{txn.discrepancies.length - 2} more discrepancy items
                                </p>
                              )}
                            </div>
                          )}

                          {onNavigateToTransaction && (
                            <button
                              onClick={() => {
                                onClose();
                                onNavigateToTransaction(txn.id);
                              }}
                              className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl bg-indigo-600/15 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-bold border border-indigo-500/30 transition cursor-pointer"
                            >
                              <span>Inspect Transaction & Audit</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-6 text-center border border-slate-800 rounded-2xl bg-slate-950/40 text-slate-500 text-xs">
                    No transactions clustered. Upload cross-referenced PO, Invoice, Delivery Note, or Payment Receipt documents.
                  </div>
                )}
              </div>

            </div>
          ) : (
            /* VIEW: UPLOAD & PROGRESS TABLE */
            <div className="space-y-6">
              
              {/* Dropzone Area */}
              <div 
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleFilesSelected(e.dataTransfer.files);
                }}
                onClick={() => !isProcessing && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-7 text-center transition-all ${
                  isProcessing 
                    ? 'border-slate-800 bg-slate-950/30 opacity-60 cursor-not-allowed'
                    : 'border-indigo-500/30 hover:border-indigo-500/60 bg-indigo-950/10 hover:bg-indigo-950/20 cursor-pointer'
                }`}
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  multiple 
                  accept=".pdf,.png,.jpg,.jpeg,image/png,image/jpeg,application/pdf" 
                  className="hidden" 
                  onChange={(e) => handleFilesSelected(e.target.files)}
                  disabled={isProcessing}
                />
                
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3">
                  <UploadCloud className="w-6 h-6 text-indigo-400" />
                </div>
                
                <p className="text-sm font-bold text-slate-200">
                  Drag and drop files here, or click to browse
                </p>
                
                <div className="flex items-center justify-center gap-2 mt-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">PDF</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">PNG</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">JPG</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">JPEG</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1.5">
                  Select multi-document batches belonging to single or multiple MSME transactions
                </p>
              </div>

              {/* Selected / Ingesting Files Table */}
              {fileItems.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <ListOrdered className="w-4 h-4 text-indigo-400" />
                      <span>Document Batch Queue ({fileItems.length})</span>
                    </h4>
                    {!isProcessing && (
                      <button 
                        onClick={handleClearAll}
                        className="text-[11px] text-slate-500 hover:text-rose-400 transition"
                      >
                        Clear All
                      </button>
                    )}
                  </div>

                  <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/60">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
                            <th className="py-3 px-4">Filename</th>
                            <th className="py-3 px-3">Size</th>
                            <th className="py-3 px-3">Document Type</th>
                            <th className="py-3 px-3 text-center">Upload</th>
                            <th className="py-3 px-3 text-center">Extraction</th>
                            <th className="py-3 px-3 text-center">Classification</th>
                            <th className="py-3 px-3 text-center">Overall Status</th>
                            <th className="py-3 px-2 text-right"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {fileItems.map((item) => {
                            const isImage = item.filename.match(/\.(png|jpg|jpeg)$/i);

                            return (
                              <React.Fragment key={item.id}>
                                <tr className="hover:bg-slate-900/40 transition">
                                  
                                  {/* Filename */}
                                  <td className="py-3 px-4 font-medium text-slate-200">
                                    <div className="flex items-center gap-2 max-w-[180px] sm:max-w-xs">
                                      {isImage ? (
                                        <ImageIcon className="w-4 h-4 text-amber-400 shrink-0" />
                                      ) : (
                                        <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                                      )}
                                      <span className="truncate font-mono text-[11px]">{item.filename}</span>
                                    </div>
                                  </td>

                                  {/* Size */}
                                  <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                                    {formatFileSize(item.size)}
                                  </td>

                                  {/* Document Type */}
                                  <td className="py-3 px-3">
                                    {item.documentType ? (
                                      <DocTypeBadge 
                                        type={item.documentType} 
                                        confidence={item.classificationConfidence} 
                                      />
                                    ) : (
                                      <span className="text-[11px] text-slate-500 italic">
                                        Auto-Detect
                                      </span>
                                    )}
                                  </td>

                                  {/* Upload Status */}
                                  <td className="py-3 px-3 text-center">
                                    <ProcessStatusBadge status={item.uploadStatus} />
                                  </td>

                                  {/* Extraction Status */}
                                  <td className="py-3 px-3 text-center">
                                    <div className="flex flex-col items-center gap-0.5">
                                      <ProcessStatusBadge status={item.extractionStatus} />
                                      {item.extractedPageCount !== undefined && item.extractedPageCount > 0 && (
                                        <span className="text-[9px] text-slate-500">
                                          {item.extractedPageCount} pg &bull; {item.extractedItemCount || 0} items
                                        </span>
                                      )}
                                    </div>
                                  </td>

                                  {/* Classification Status */}
                                  <td className="py-3 px-3 text-center">
                                    <ProcessStatusBadge status={item.classificationStatus} />
                                  </td>

                                  {/* Overall Status */}
                                  <td className="py-3 px-3 text-center">
                                    <ProcessStatusBadge status={item.overallStatus} />
                                  </td>

                                  {/* Action */}
                                  <td className="py-3 px-2 text-right">
                                    {!isProcessing && (
                                      <button
                                        onClick={() => handleRemoveFile(item.id)}
                                        className="p-1 text-slate-500 hover:text-rose-400 rounded-lg transition"
                                      >
                                        <X className="w-3.5 h-3.5" />
                                      </button>
                                    )}
                                  </td>

                                </tr>

                                {/* Expandable Error Detail Row */}
                                {item.errorMessage && (
                                  <tr className="bg-rose-950/20">
                                    <td colSpan={8} className="py-2 px-4 border-t border-rose-500/20">
                                      <div className="flex items-center gap-2 text-[11px] text-rose-400 font-mono">
                                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                                        <span><b>Processing Error:</b> {item.errorMessage}</span>
                                      </div>
                                    </td>
                                  </tr>
                                )}

                              </React.Fragment>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

            </div>
          )}

        </div>

        {/* Footer Controls */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950/80 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition"
          >
            {currentStep === 'RESULTS' ? 'Close' : 'Cancel'}
          </button>

          {currentStep === 'RESULTS' ? (
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-6 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-600/25 transition cursor-pointer"
            >
              <span>View All Documents & Transactions</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleStartWorkflow}
              disabled={fileItems.length === 0 || isProcessing || fileItems.every(f => f.overallStatus === 'FAILED')}
              className="flex items-center gap-2 px-6 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 rounded-xl shadow-lg shadow-indigo-600/25 transition-all cursor-pointer"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing Step: {currentStep}...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Start Pipeline & Reconcile ({fileItems.filter(f => f.overallStatus !== 'FAILED').length} Files)</span>
                </>
              )}
            </button>
          )}
        </div>

      </div>
    </div>
  );
};
