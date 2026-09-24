import React, { useEffect } from 'react';
import { 
  X, 
  AlertTriangle, 
  FileSearch, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  FileText, 
  Layers,
  HelpCircle
} from 'lucide-react';
import type { DiscrepancyItem } from '../../types';
import { SeverityBadge } from '../common/Badge';

interface EvidenceViewerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  discrepancy: DiscrepancyItem | null;
}

export const EvidenceViewerDrawer: React.FC<EvidenceViewerDrawerProps> = ({
  isOpen,
  onClose,
  discrepancy
}) => {
  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !discrepancy) return null;

  const confPercent = Math.round(discrepancy.confidence * 100);

  // Fallback calculations for expected / actual if empty
  const expectedDisplay = discrepancy.expected_value || (
    discrepancy.evidences.length > 0 ? discrepancy.evidences[0].exact_value : 'Contract Standard'
  );
  const actualDisplay = discrepancy.actual_value || (
    discrepancy.evidences.length > 1 ? discrepancy.evidences[1].exact_value : (
      discrepancy.difference_amount > 0 ? `₹${discrepancy.difference_amount.toLocaleString('en-IN')}` : 'Deviated Value'
    )
  );
  const diffDisplay = discrepancy.difference_value || (
    discrepancy.difference_amount > 0 ? `₹${discrepancy.difference_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'Variance Flagged'
  );

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
          
          {/* Drawer Header */}
          <div className="p-6 border-b border-slate-800 bg-slate-950/60 flex items-start justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/80 px-2.5 py-0.5 rounded-md border border-indigo-500/30 uppercase tracking-wider">
                  {discrepancy.rule_code}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  • {discrepancy.discrepancy_type}
                </span>
                <SeverityBadge severity={discrepancy.severity} />
              </div>
              <h3 className="text-lg font-extrabold text-slate-100">
                {discrepancy.title}
              </h3>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
              title="Close Panel (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* 1. Derivation Summary: Expected vs Actual vs Difference */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span>Mathematical Derivation & Values</span>
                </h4>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span>Confidence:</span>
                  <span className="font-mono font-bold text-emerald-400">{confPercent}%</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                
                {/* Expected Value Card */}
                <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                      Expected Value
                    </span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <p className="text-lg font-mono font-extrabold text-emerald-300 break-words">
                    {expectedDisplay}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    Baseline agreement / PO standard
                  </p>
                </div>

                {/* Actual Value Card */}
                <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/30 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">
                      Actual Value
                    </span>
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  </div>
                  <p className="text-lg font-mono font-extrabold text-rose-300 break-words">
                    {actualDisplay}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    Billed / recorded in document
                  </p>
                </div>

                {/* Difference Value Card */}
                <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                      Difference
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <p className="text-lg font-mono font-extrabold text-amber-300 break-words">
                    {diffDisplay}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    Reconciliation variance
                  </p>
                </div>

              </div>
            </div>

            {/* 2. Discrepancy Description & Rule Logic */}
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
              <h5 className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4 text-slate-400" />
                <span>Audit Finding Description</span>
              </h5>
              <p className="text-xs text-slate-300 leading-relaxed">
                {discrepancy.description}
              </p>
            </div>

            {/* 3. AI Decision Support Explanation */}
            {discrepancy.llm_explanation && (
              <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 space-y-2">
                <div className="flex items-center gap-2 text-indigo-300 font-bold text-xs">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>AI Grounded Explanation & Financial Impact</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  {discrepancy.llm_explanation}
                </p>
              </div>
            )}

            {/* 4. Multi-Document Source Evidence Citations */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <FileSearch className="w-4 h-4 text-indigo-400" />
                  <span>Document Evidence Citations ({discrepancy.evidences.length})</span>
                </h4>
                <span className="text-[11px] text-slate-400 font-mono">
                  Exact extracted snippets
                </span>
              </div>

              {discrepancy.evidences.length > 0 ? (
                <div className="space-y-3">
                  {discrepancy.evidences.map((ev, idx) => (
                    <div 
                      key={ev.id || idx}
                      className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3 hover:border-slate-700 transition"
                    >
                      {/* Document Meta Header */}
                      <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-slate-200 truncate">
                              {ev.document_name}
                            </p>
                            <p className="text-[10px] text-slate-400 font-mono">
                              Page {ev.page_number} • Target Field: <span className="text-indigo-300 font-semibold">{ev.field_name}</span>
                            </p>
                          </div>
                        </div>

                        <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
                          {Math.round((ev.relevance_score ?? 1.0) * 100)}% Match
                        </span>
                      </div>

                      {/* Extracted Exact Value */}
                      {ev.exact_value && (
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-slate-400 text-[11px]">Extracted Token:</span>
                          <span className="font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                            {ev.exact_value}
                          </span>
                        </div>
                      )}

                      {/* Text Snippet OCR Context */}
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
                          Source Text Snippet:
                        </span>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-slate-200 leading-relaxed break-words">
                          "{ev.snippet}"
                        </div>
                      </div>

                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center rounded-2xl bg-slate-950/40 border border-slate-800 text-slate-400 text-xs">
                  No text snippets attached to this finding.
                </div>
              )}
            </div>

            {/* 5. Derivation Workflow Audit Chain */}
            <div className="p-4 rounded-2xl bg-slate-950/40 border border-slate-800 space-y-3">
              <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Derivation Audit Chain
              </h5>
              
              <div className="space-y-2 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-indigo-400 flex items-center justify-center font-mono font-bold text-[10px]">1</span>
                  <span>Extracted key-value pair and line items from source document text.</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-indigo-400 flex items-center justify-center font-mono font-bold text-[10px]">2</span>
                  <span>Normalized numerical figures into strict Python <code className="text-indigo-300 font-mono">Decimal</code> format.</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-indigo-400 flex items-center justify-center font-mono font-bold text-[10px]">3</span>
                  <span>Evaluated deterministic rule <code className="text-amber-300 font-mono">{discrepancy.rule_code}</code> against expected baselines.</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-emerald-400 flex items-center justify-center font-mono font-bold text-[10px]">4</span>
                  <span>Flagged discrepancy with verifiable mathematical variance.</span>
                </div>
              </div>
            </div>

          </div>

          {/* Drawer Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono">
              Status: <b className="text-slate-200">{discrepancy.status}</b>
            </span>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition cursor-pointer"
            >
              Close Inspector
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};
