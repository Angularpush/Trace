import React from 'react';
import { 
  FileText, 
  Truck, 
  Receipt, 
  CreditCard, 
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  GitBranch,
  ShieldCheck,
  Zap,
  Sparkles
} from 'lucide-react';
import type { DocumentItem, TransactionGraphEdge } from '../../types';

interface TransactionFlowGraphProps {
  documents: DocumentItem[];
  edges?: TransactionGraphEdge[];
}

export const TransactionFlowGraph: React.FC<TransactionFlowGraphProps> = ({ documents, edges = [] }) => {
  const steps = [
    { type: 'PURCHASE_ORDER', label: '1. Purchase Order', icon: FileText, desc: 'Contracted Price & Quantity' },
    { type: 'DELIVERY_NOTE', label: '2. Delivery Note', icon: Truck, desc: 'Physical Goods Received' },
    { type: 'INVOICE', label: '3. Tax Invoice', icon: Receipt, desc: 'Commercial Billing' },
    { type: 'PAYMENT_RECEIPT', label: '4. Payment Record', icon: CreditCard, desc: 'Financial Settlement' },
  ];

  const getDocForType = (type: string) => {
    return documents.find(d => (d.document_type || d.doc_type) === type);
  };

  const unmappedDocs = documents.filter(d => !steps.some(s => s.type === (d.document_type || d.doc_type)));

  const getMethodBadge = (method: string) => {
    switch (method?.toLowerCase()) {
      case 'exact_identifier':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1"><ShieldCheck className="w-2.5 h-2.5"/> Exact ID</span>;
      case 'metadata_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1"><Zap className="w-2.5 h-2.5"/> Metadata</span>;
      case 'semantic_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1"><Sparkles className="w-2.5 h-2.5"/> Semantic</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1"><GitBranch className="w-2.5 h-2.5"/> Hybrid</span>;
    }
  };

  return (
    <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-indigo-400" />
            <span>Multi-Signal Transaction Linking Graph</span>
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Exact Identifiers (PO/Inv/Ref) &bull; Metadata Matching (Supplier/Amount) &bull; Semantic Vector Alignment
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-indigo-300 bg-indigo-950/60 px-3 py-1 rounded-xl border border-indigo-500/30">
            {documents.length} Document(s) Ingested
          </span>
        </div>
      </div>

      {/* Visual Pipeline with Sequential Flow */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
        {steps.map((step, idx) => {
          const doc = getDocForType(step.type);
          const Icon = step.icon;
          const isPresent = !!doc;
          const docEdge = doc ? edges.find(e => e.document_id === doc.id || e.to_doc_id === doc.id || e.from_doc_id === doc.id) : null;

          return (
            <div key={step.type} className="relative flex flex-col">
              <div 
                className={`p-4 rounded-2xl border transition-all h-full flex flex-col justify-between ${
                  isPresent 
                    ? 'bg-slate-950/80 border-indigo-500/40 text-slate-100 shadow-md shadow-indigo-500/5' 
                    : 'bg-slate-950/30 border-slate-800/80 text-slate-500 opacity-60'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2.5 rounded-xl ${isPresent ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20' : 'bg-slate-900 text-slate-600'}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    {isPresent ? (
                      <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Present</span>
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                        <AlertCircle className="w-3 h-3" />
                        <span>Missing</span>
                      </span>
                    )}
                  </div>

                  <h5 className="text-xs font-bold text-slate-100">{step.label}</h5>
                  <p className="text-[11px] text-slate-400 truncate mt-1">
                    {doc ? doc.filename : step.desc}
                  </p>
                  
                  {doc?.page_start && doc?.page_end && (
                    <span className="inline-block mt-1 text-[10px] text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded">
                      Pages {doc.page_start} - {doc.page_end}
                    </span>
                  )}
                </div>

                {/* Link Provenance & Metadata Chips */}
                <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1.5">
                  {doc?.parsed_data?.document_number ? (
                    <p className="text-[10px] font-mono text-indigo-300 truncate">
                      <b>Ref:</b> {doc.parsed_data.document_number}
                    </p>
                  ) : null}

                  {docEdge && (
                    <div className="flex items-center justify-between pt-1">
                      {getMethodBadge(docEdge.link_method)}
                      <span className="text-[10px] font-mono font-bold text-slate-400">
                        {(docEdge.link_confidence * 100).toFixed(0)}% Conf
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Connecting Flow Arrow */}
              {idx < steps.length - 1 && (
                <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 items-center justify-center text-slate-400">
                  <ArrowRight className="w-3 h-3" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Unmapped Supporting Documents */}
      {unmappedDocs.length > 0 && (
        <div className="pt-2 border-t border-slate-800/60">
          <p className="text-xs font-bold text-slate-400 mb-2">Supporting Linked Documents ({unmappedDocs.length})</p>
          <div className="flex flex-wrap gap-2">
            {unmappedDocs.map(d => (
              <span key={d.id} className="text-xs px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>{d.document_type || d.doc_type}: {d.filename}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
