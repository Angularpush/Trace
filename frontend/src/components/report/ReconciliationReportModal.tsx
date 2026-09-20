import React from 'react';
import { 
  X, 
  Printer, 
  Download, 
  ShieldCheck, 
  CheckCircle2
} from 'lucide-react';
import type { ReconciliationSummaryReport } from '../../types';
import { SeverityBadge, StatusBadge } from '../common/Badge';

interface ReconciliationReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: ReconciliationSummaryReport;
}

export const ReconciliationReportModal: React.FC<ReconciliationReportModalProps> = ({ isOpen, onClose, report }) => {
  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `TRACE_Reconciliation_Report_${report.transaction_ref}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden my-8 animate-in fade-in zoom-in duration-200">
        
        {/* Modal Controls Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50 print:hidden">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-slate-100">Audit & Decision Support Report</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-200 rounded-lg transition ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Formal Printable Document Content */}
        <div className="p-8 space-y-6 text-slate-100 bg-slate-900 print:bg-white print:text-black">
          
          {/* Header */}
          <div className="flex justify-between items-start border-b border-slate-800 pb-6 print:border-gray-300">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-extrabold text-indigo-400 print:text-blue-900">TRACE</span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-500/30 print:border-gray-400">
                  Audit Report
                </span>
              </div>
              <p className="text-xs text-slate-400 print:text-gray-600 mt-1">
                Document-Level MSME Transaction Reconciliation & Discrepancy Detection
              </p>
            </div>
            <div className="text-right text-xs text-slate-400 print:text-gray-600 space-y-0.5 font-mono">
              <p><b>Transaction Ref:</b> {report.transaction_ref}</p>
              <p><b>Reconciled At:</b> {new Date(report.generated_at).toLocaleString()}</p>
              <p><b>Audit Mode:</b> {report.mode_used}</p>
            </div>
          </div>

          {/* Status & Financial Summary Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 print:border-gray-300">
              <p className="text-xs text-slate-400 print:text-gray-600 uppercase font-semibold">Audit Status</p>
              <div className="mt-1">
                <StatusBadge status={report.reconciliation_status} />
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 print:border-gray-300">
              <p className="text-xs text-slate-400 print:text-gray-600 uppercase font-semibold">Total Discrepancies</p>
              <p className="text-xl font-extrabold text-slate-100 print:text-black mt-0.5">
                {report.total_discrepancies}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 print:border-gray-300">
              <p className="text-xs text-slate-400 print:text-gray-600 uppercase font-semibold">Net Financial Variance</p>
              <p className="text-xl font-extrabold text-rose-400 print:text-red-700 font-mono mt-0.5">
                ₹{report.financial_variance_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* AI Decision Support Summary */}
          <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 print:border-gray-300 print:bg-gray-50">
            <h5 className="text-xs font-bold uppercase tracking-wider text-indigo-300 print:text-blue-900 mb-1.5">
              Decision Support Executive Summary
            </h5>
            <p className="text-xs text-slate-300 print:text-gray-800 leading-relaxed font-sans">
              {report.ai_grounded_explanation}
            </p>
          </div>

          {/* Discrepancy Table */}
          <div className="space-y-3">
            <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 print:text-gray-700">
              Itemized Discrepancy Findings
            </h5>
            
            {report.discrepancies.length > 0 ? (
              <div className="border border-slate-800 rounded-xl overflow-hidden print:border-gray-300">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950/80 border-b border-slate-800 print:bg-gray-100 text-slate-400 print:text-gray-700">
                      <th className="p-3 font-semibold">Rule Code</th>
                      <th className="p-3 font-semibold">Severity</th>
                      <th className="p-3 font-semibold">Finding / Title</th>
                      <th className="p-3 font-semibold text-right">Variance</th>
                      <th className="p-3 font-semibold text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 print:divide-gray-200">
                    {report.discrepancies.map((d, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="p-3 font-mono font-medium text-slate-300">{d.rule_code}</td>
                        <td className="p-3"><SeverityBadge severity={d.severity} /></td>
                        <td className="p-3">
                          <p className="font-bold text-slate-200">{d.title}</p>
                          <p className="text-[11px] text-slate-400 mt-0.5">{d.description}</p>
                        </td>
                        <td className="p-3 text-right font-mono font-bold text-rose-400">
                          {d.difference_amount > 0 ? `₹${d.difference_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                        </td>
                        <td className="p-3 text-right font-mono text-slate-300">
                          {Math.round(d.confidence * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Zero discrepancies detected. Multi-document transaction is 100% reconciled.</span>
              </div>
            )}
          </div>

          {/* Audit Disclaimer */}
          <div className="text-[10px] text-slate-500 print:text-gray-500 border-t border-slate-800 pt-4 print:border-gray-200 space-y-1">
            <p>
              <b>TRACE Decision-Support System:</b> This automated reconciliation report identifies inconsistencies and presents grounded evidence for human auditor investigation. It does not constitute legal or tax filing advice.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
};
