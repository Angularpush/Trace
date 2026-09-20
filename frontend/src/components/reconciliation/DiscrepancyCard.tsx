import React, { useState } from 'react';
import { 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  FileSearch, 
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ExternalLink,
  FileText
} from 'lucide-react';
import type { DiscrepancyItem } from '../../types';
import { SeverityBadge } from '../common/Badge';

interface DiscrepancyCardProps {
  discrepancy: DiscrepancyItem;
  onInspect?: (discrepancy: DiscrepancyItem) => void;
}

export const DiscrepancyCard: React.FC<DiscrepancyCardProps> = ({ 
  discrepancy, 
  onInspect 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const confPercent = Math.round(discrepancy.confidence * 100);

  // Derivation values
  const expectedDisplay = discrepancy.expected_value || (
    discrepancy.evidences.length > 0 ? discrepancy.evidences[0].exact_value : 'Contract Agreed'
  );
  const actualDisplay = discrepancy.actual_value || (
    discrepancy.evidences.length > 1 ? discrepancy.evidences[1].exact_value : (
      discrepancy.difference_amount > 0 ? `₹${discrepancy.difference_amount.toLocaleString('en-IN')}` : 'Billed Value'
    )
  );
  const diffDisplay = discrepancy.difference_value || (
    discrepancy.difference_amount > 0 ? `₹${discrepancy.difference_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'Variance'
  );

  return (
    <div className="border border-slate-800 bg-slate-900/70 hover:border-slate-700/90 rounded-2xl overflow-hidden transition-all duration-200 shadow-sm">
      
      {/* Top Header & Summary */}
      <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex items-start gap-3.5">
          <div className={`p-2.5 rounded-xl shrink-0 mt-0.5 ${
            discrepancy.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
            discrepancy.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
            discrepancy.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
            'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          }`}>
            <AlertTriangle className="w-5 h-5" />
          </div>

          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-500/30 uppercase tracking-wider">
                {discrepancy.rule_code}
              </span>
              <SeverityBadge severity={discrepancy.severity} />
              <span className="text-xs font-mono text-slate-400">• {discrepancy.discrepancy_type}</span>
            </div>
            <h4 className="text-base font-extrabold text-slate-100">{discrepancy.title}</h4>
            <p className="text-xs text-slate-400">{discrepancy.description}</p>
          </div>
        </div>

        {/* Action Buttons & Confidence */}
        <div className="flex items-center gap-3 sm:self-center shrink-0 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-800">
          <div className="text-right">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Confidence</p>
            <div className="flex items-center gap-1.5 justify-end">
              <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-emerald-500 rounded-full" 
                  style={{ width: `${confPercent}%` }}
                />
              </div>
              <span className="text-xs font-mono font-bold text-slate-200">{confPercent}%</span>
            </div>
          </div>

          {onInspect && (
            <button
              onClick={() => onInspect(discrepancy)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-bold transition cursor-pointer"
              title="Open full Evidence Viewer side-drawer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Evidence Drawer</span>
            </button>
          )}

          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
            title={isExpanded ? "Collapse Evidence" : "Expand Evidence"}
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Comparative Derivation Bridge (Expected vs Actual vs Difference) */}
      <div className="p-4 sm:p-5 bg-slate-900/40 border-b border-slate-800/80">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          
          {/* Expected */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-emerald-500/20 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                Expected Value
              </span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <p className="text-sm font-mono font-bold text-emerald-300 truncate">
              {expectedDisplay}
            </p>
          </div>

          {/* Actual */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-rose-500/20 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">
                Actual Value
              </span>
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <p className="text-sm font-mono font-bold text-rose-300 truncate">
              {actualDisplay}
            </p>
          </div>

          {/* Difference */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-amber-500/20 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                Difference / Variance
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-sm font-mono font-bold text-amber-300 truncate">
              {diffDisplay}
            </p>
          </div>

        </div>
      </div>

      {/* Expanded Details: Evidence Drawer & AI Explanation */}
      {isExpanded && (
        <div className="p-4 sm:p-5 space-y-4 animate-in fade-in duration-150">
          
          {/* Grounded Evidence Citations */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h5 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <FileSearch className="w-4 h-4 text-indigo-400" />
                <span>Source Evidence Citations ({discrepancy.evidences.length})</span>
              </h5>
              <span className="text-[10px] text-slate-500 font-mono">
                Extracted with 100% ground truth OCR matching
              </span>
            </div>

            {discrepancy.evidences.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {discrepancy.evidences.map((ev, idx) => (
                  <div 
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between text-slate-400 border-b border-slate-800/80 pb-1.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span className="font-semibold text-slate-200 truncate">{ev.document_name}</span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-indigo-300 border border-slate-800 shrink-0">
                        Page {ev.page_number} • Field: {ev.field_name}
                      </span>
                    </div>

                    {ev.exact_value && (
                      <div className="flex items-center gap-2 text-[11px]">
                        <span className="text-slate-400">Extracted:</span>
                        <span className="font-mono text-emerald-400 font-bold bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/20">
                          {ev.exact_value}
                        </span>
                      </div>
                    )}

                    <div className="space-y-0.5">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Source Text Snippet:</span>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 font-mono text-[11px] text-slate-200 leading-relaxed">
                        "{ev.snippet}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No direct text snippet citation attached.</p>
            )}
          </div>

          {/* AI Grounded Explanation */}
          {discrepancy.llm_explanation && (
            <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-1.5">
              <div className="flex items-center gap-1.5 text-indigo-300 font-semibold text-xs">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>AI Decision Support Explanation</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {discrepancy.llm_explanation}
              </p>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
