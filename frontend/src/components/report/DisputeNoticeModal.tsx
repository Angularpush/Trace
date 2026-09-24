import React, { useState } from 'react';
import { 
  X, 
  Printer, 
  Copy, 
  Check, 
  FileWarning, 
  Download, 
  Building2, 
  Calendar, 
  BadgeAlert,
  FileText
} from 'lucide-react';
import type { DisputeNoticeResponse } from '../../types';

interface DisputeNoticeModalProps {
  isOpen: boolean;
  onClose: () => void;
  disputeNotice: DisputeNoticeResponse | null;
  isLoading?: boolean;
}

export const DisputeNoticeModal: React.FC<DisputeNoticeModalProps> = ({
  isOpen,
  onClose,
  disputeNotice,
  isLoading = false
}) => {
  const [copied, setCopied] = useState(false);
  const [viewRawMarkdown, setViewRawMarkdown] = useState(false);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleCopyMarkdown = () => {
    if (!disputeNotice) return;
    navigator.clipboard.writeText(disputeNotice.formal_letter_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownloadMarkdown = () => {
    if (!disputeNotice) return;
    const blob = new Blob([disputeNotice.formal_letter_markdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${disputeNotice.dispute_reference}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden my-8 animate-in fade-in zoom-in duration-200">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60 print:hidden">
          <div className="flex items-center gap-2.5">
            <FileWarning className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-base font-bold text-slate-100">Formal Vendor Dispute & Withholding Notice</h3>
              <p className="text-[11px] text-slate-400">Statutory Notice of Financial Discrepancy & Credit Note Demand</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewRawMarkdown(!viewRawMarkdown)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{viewRawMarkdown ? 'Formatted View' : 'Markdown View'}</span>
            </button>
            <button
              onClick={handleCopyMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied Notice' : 'Copy Notice'}</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Save .md</span>
            </button>
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg transition ml-2 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            Generating legal dispute notice and computing itemized financial variances...
          </div>
        ) : !disputeNotice ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No dispute notice generated for this transaction.
          </div>
        ) : viewRawMarkdown ? (
          <div className="p-6 bg-slate-950 font-mono text-xs text-slate-300 max-h-[70vh] overflow-y-auto whitespace-pre-wrap">
            {disputeNotice.formal_letter_markdown}
          </div>
        ) : (
          <div className="p-8 space-y-6 text-slate-100 bg-slate-900 print:bg-white print:text-black max-h-[75vh] overflow-y-auto">
            
            {/* Notice Header */}
            <div className="flex justify-between items-start border-b border-slate-800 pb-6 print:border-gray-300">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-black text-rose-400 print:text-rose-800">TRACE AUDIT DIVISION</span>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-500/30">
                    Formal Dispute Notice
                  </span>
                </div>
                <h2 className="text-sm font-semibold text-slate-300 mt-1">
                  Reference: <span className="font-mono text-amber-400 font-bold">{disputeNotice.dispute_reference}</span>
                </h2>
              </div>
              <div className="text-right text-xs text-slate-400 space-y-1">
                <p className="flex items-center justify-end gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span><b>Date:</b> {disputeNotice.audit_date}</span>
                </p>
                <p><b>Transaction Ref:</b> <span className="font-mono text-slate-200">{disputeNotice.transaction_reference}</span></p>
              </div>
            </div>

            {/* Parties: TO & FROM */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950/40 border border-slate-800 print:border-gray-300 print:bg-gray-50">
              <div className="space-y-1 text-xs">
                <span className="text-[10px] uppercase font-bold text-slate-400">TO (Vendor / Supplier):</span>
                <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-indigo-400" />
                  <span>{disputeNotice.supplier_name}</span>
                </p>
                <p className="text-slate-400">Accounts Receivable & Billing Department</p>
              </div>
              <div className="space-y-1 text-xs">
                <span className="text-[10px] uppercase font-bold text-slate-400">FROM (Customer / Buyer):</span>
                <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-emerald-400" />
                  <span>{disputeNotice.customer_name}</span>
                </p>
                <p className="text-slate-400">Internal Audit & Accounts Payable Division</p>
              </div>
            </div>

            {/* Financial Withholding Summary Box */}
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                  <BadgeAlert className="w-4 h-4 text-rose-400" />
                  <span>Total Disputed Sum Subject to Withholding</span>
                </div>
                <p className="text-xs text-slate-300">
                  {disputeNotice.total_discrepancies} actionable discrepancy finding(s) detected during automated 3-way multi-document audit.
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black font-mono text-rose-400">
                  ₹{disputeNotice.total_variance_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <span className="text-[10px] text-rose-300 uppercase font-bold">Payment Withheld Pending Resolution</span>
              </div>
            </div>

            {/* Discrepancy Findings Table */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                1. Itemized Schedule of Discrepancies
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3">Finding</th>
                      <th className="py-2.5 px-3">Expected (PO / Contract)</th>
                      <th className="py-2.5 px-3">Actual (Invoice / Billed)</th>
                      <th className="py-2.5 px-3">Variance</th>
                      <th className="py-2.5 px-3">Audit Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono text-slate-200">
                    {disputeNotice.discrepancies.map((d, i) => (
                      <tr key={i} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 text-slate-400">{i + 1}</td>
                        <td className="py-2.5 px-3 font-sans font-semibold text-slate-100">
                          {d.title}
                          <span className="block text-[10px] font-mono text-amber-400">{d.discrepancy_type}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">{d.expected_value}</td>
                        <td className="py-2.5 px-3 text-rose-300">{d.actual_value}</td>
                        <td className="py-2.5 px-3 font-bold text-rose-400">{d.variance_amount}</td>
                        <td className="py-2.5 px-3 font-sans text-[11px] text-slate-400 max-w-xs">{d.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action Required / Terms */}
            <div className="space-y-2 p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-xs">
              <h4 className="font-bold text-slate-200 uppercase text-[11px]">2. Required Corrective Actions</h4>
              <ol className="list-decimal list-inside space-y-1.5 text-slate-300 leading-relaxed">
                <li><b>Payment Withholding</b>: Payment of <b>₹{disputeNotice.total_variance_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</b> is withheld until an amended invoice or credit note is supplied.</li>
                <li><b>Credit Note Issuance</b>: Vendor must issue a valid Credit Note for the disputed variance within five (5) business days.</li>
                <li><b>Document Rectification</b>: Submit revised Goods Received Notes (GRN) or purchase order amendments matching agreed contract terms.</li>
              </ol>
            </div>

            {/* Notice Footer / Sign-off */}
            <div className="pt-4 border-t border-slate-800 text-xs text-slate-400 flex justify-between items-end">
              <div>
                <p className="font-bold text-slate-200">Accounts Payable & Internal Audit Committee</p>
                <p>{disputeNotice.customer_name}</p>
              </div>
              <div className="text-right text-[11px] text-slate-500 font-mono">
                Generated by TRACE MSME Multi-Document Engine
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
};

