import React from 'react';
import { 
  FileText, 
  Truck, 
  Receipt, 
  CreditCard, 
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowDown
} from 'lucide-react';
import type { DocumentItem } from '../../types';

interface TransactionFlowGraphProps {
  documents: DocumentItem[];
}

export const TransactionFlowGraph: React.FC<TransactionFlowGraphProps> = ({ documents }) => {
  const steps = [
    { type: 'PURCHASE_ORDER', label: '1. Purchase Order', icon: FileText, desc: 'Contracted Price & Quantity' },
    { type: 'DELIVERY_NOTE', label: '2. Delivery Note', icon: Truck, desc: 'Physical Goods Received' },
    { type: 'INVOICE', label: '3. Tax Invoice', icon: Receipt, desc: 'Commercial Billing' },
    { type: 'PAYMENT_RECEIPT', label: '4. Payment Record', icon: CreditCard, desc: 'Financial Settlement' },
  ];

  const getDocForType = (type: string) => {
    return documents.find(d => d.doc_type === type);
  };

  return (
    <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
            <span>4-Stage Document Reconciliation Lifecycle</span>
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Purchase Order &rarr; Delivery Note &rarr; Tax Invoice &rarr; Payment Record
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-indigo-300 bg-indigo-950/60 px-3 py-1 rounded-xl border border-indigo-500/30 self-start sm:self-auto">
          {documents.length} / 4 Documents Ingested
        </span>
      </div>

      {/* Visual Pipeline with Sequential Flow */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
        {steps.map((step, idx) => {
          const doc = getDocForType(step.type);
          const Icon = step.icon;
          const isPresent = !!doc;
          const grandTotal = doc?.parsed_data?.grand_total || doc?.parsed_data?.payment_amount;

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
                </div>

                {/* Document Metadata Chips */}
                <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1">
                  {doc?.parsed_data?.document_number ? (
                    <p className="text-[10px] font-mono text-indigo-300 truncate">
                      <b>Ref:</b> {doc.parsed_data.document_number}
                    </p>
                  ) : doc?.parsed_data?.po_reference ? (
                    <p className="text-[10px] font-mono text-indigo-300 truncate">
                      <b>PO Ref:</b> {doc.parsed_data.po_reference}
                    </p>
                  ) : null}

                  {grandTotal !== undefined && Number(grandTotal) > 0 ? (
                    <p className="text-[11px] font-mono font-bold text-emerald-400">
                      ₹{Number(grandTotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  ) : null}
                </div>
              </div>

              {/* Desktop Flow Arrow */}
              {idx < steps.length - 1 && (
                <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-800 border border-slate-700 items-center justify-center text-slate-400 shadow-md">
                  <ArrowRight className="w-3 h-3" />
                </div>
              )}

              {/* Mobile Flow Arrow */}
              {idx < steps.length - 1 && (
                <div className="md:hidden flex justify-center py-1 text-slate-600">
                  <ArrowDown className="w-4 h-4" />
                </div>
              )}

            </div>
          );
        })}
      </div>
    </div>
  );
};
