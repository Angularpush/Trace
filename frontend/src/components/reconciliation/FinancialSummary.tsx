import React from 'react';
import { 
  DollarSign, 
  Receipt, 
  CreditCard, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import type { DocumentItem, DiscrepancyItem } from '../../types';

interface FinancialSummaryProps {
  documents: DocumentItem[];
  discrepancies: DiscrepancyItem[];
  totalAmount?: number;
}

export const FinancialSummary: React.FC<FinancialSummaryProps> = ({ 
  documents, 
  discrepancies,
  totalAmount 
}) => {
  const poDoc = documents.find(d => d.doc_type === 'PURCHASE_ORDER');
  const invDoc = documents.find(d => d.doc_type === 'INVOICE');
  const dnDoc = documents.find(d => d.doc_type === 'DELIVERY_NOTE');
  const payDoc = documents.find(d => d.doc_type === 'PAYMENT_RECEIPT');

  // Extract financial values
  const parseNum = (val: any): number => {
    if (val === null || val === undefined) return 0;
    const clean = String(val).replace(/[^0-9.-]+/g, '');
    const num = parseFloat(clean);
    return isNaN(num) ? 0 : num;
  };

  const poTotal = parseNum(poDoc?.parsed_data?.grand_total || poDoc?.parsed_data?.subtotal);
  const invoiceTotal = parseNum(invDoc?.parsed_data?.grand_total || totalAmount || 0);
  const invoiceSubtotal = parseNum(invDoc?.parsed_data?.subtotal);
  const invoiceTax = parseNum(invDoc?.parsed_data?.tax_total);
  const paidTotal = parseNum(payDoc?.parsed_data?.payment_amount || payDoc?.parsed_data?.grand_total);
  
  // Calculate delivered value based on DN items matched to PO/Invoice unit prices
  let deliveredValue = 0;
  if (dnDoc?.parsed_data?.items && dnDoc.parsed_data.items.length > 0) {
    deliveredValue = dnDoc.parsed_data.items.reduce((sum, item) => {
      const qty = parseNum(item.quantity);
      // Find matching item unit price in PO or Invoice
      const matchingInvItem = invDoc?.parsed_data?.items?.find(i => 
        i.description.toLowerCase().includes(item.description.toLowerCase()) ||
        item.description.toLowerCase().includes(i.description.toLowerCase())
      );
      const matchingPoItem = poDoc?.parsed_data?.items?.find(i => 
        i.description.toLowerCase().includes(item.description.toLowerCase()) ||
        item.description.toLowerCase().includes(i.description.toLowerCase())
      );
      const unitPrice = parseNum(matchingInvItem?.unit_price || matchingPoItem?.unit_price || item.unit_price);
      return sum + (qty * unitPrice);
    }, 0);
  } else if (dnDoc) {
    // If DN has no item pricing, estimate from invoice total or po total
    deliveredValue = invoiceTotal || poTotal;
  }

  // Outstanding shortfall calculation
  const paymentShortfallDiscrepancy = discrepancies.find(d => 
    d.rule_code === 'PAYMENT_SHORTFALL' || d.discrepancy_type.includes('SHORTFALL')
  );
  const outstandingAmount = paymentShortfallDiscrepancy 
    ? paymentShortfallDiscrepancy.difference_amount 
    : Math.max(0, invoiceTotal - paidTotal);

  // Align Line Items across PO, Delivery, and Invoice
  const poItems = poDoc?.parsed_data?.items || [];
  const dnItems = dnDoc?.parsed_data?.items || [];
  const invItems = invDoc?.parsed_data?.items || [];

  // Union all unique item descriptions
  const allItemNames = Array.from(new Set([
    ...poItems.map(i => i.description.trim()),
    ...dnItems.map(i => i.description.trim()),
    ...invItems.map(i => i.description.trim())
  ]));

  const itemReconciliationRows = allItemNames.map(name => {
    const pItem = poItems.find(i => i.description.trim().toLowerCase() === name.toLowerCase());
    const dItem = dnItems.find(i => i.description.trim().toLowerCase() === name.toLowerCase());
    const iItem = invItems.find(i => i.description.trim().toLowerCase() === name.toLowerCase());

    const pQty = pItem ? parseNum(pItem.quantity) : null;
    const dQty = dItem ? parseNum(dItem.quantity) : null;
    const iQty = iItem ? parseNum(iItem.quantity) : null;

    const pPrice = pItem ? parseNum(pItem.unit_price) : null;
    const iPrice = iItem ? parseNum(iItem.unit_price) : null;

    const iTotal = iItem ? parseNum(iItem.total_amount) : (iQty && iPrice ? iQty * iPrice : null);
    const unit = iItem?.unit || pItem?.unit || dItem?.unit || 'PCS';

    // Status checks
    let status: 'MATCHED' | 'QTY_MISMATCH' | 'PRICE_MISMATCH' | 'UNDELIVERED' | 'UNBILLED' = 'MATCHED';
    let statusLabel = 'Clean Match';
    let statusColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';

    if (dQty !== null && iQty !== null && dQty !== iQty) {
      status = 'QTY_MISMATCH';
      statusLabel = `Qty Mismatch (${iQty > dQty ? 'Overbilled +' : ''}${iQty - dQty})`;
      statusColor = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    } else if (pPrice !== null && iPrice !== null && pPrice !== iPrice) {
      status = 'PRICE_MISMATCH';
      statusLabel = `Price Variance (₹${pPrice} → ₹${iPrice})`;
      statusColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    } else if (pQty !== null && iQty === null) {
      status = 'UNBILLED';
      statusLabel = 'Not Invoiced';
      statusColor = 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    } else if (pQty !== null && dQty === null && dnDoc) {
      status = 'UNDELIVERED';
      statusLabel = 'Undelivered';
      statusColor = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    }

    return {
      description: name,
      poQty: pQty,
      poPrice: pPrice,
      dnQty: dQty,
      invQty: iQty,
      invPrice: iPrice,
      invTotal: iTotal,
      unit,
      status,
      statusLabel,
      statusColor
    };
  });

  return (
    <div className="space-y-6">
      
      {/* 4 Key Financial Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* 1. Contracted PO Total */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Contracted (PO)</span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="space-y-0.5">
            <p className="text-xl font-mono font-extrabold text-slate-100">
              {poTotal > 0 ? `₹${poTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
            </p>
            <p className="text-[11px] text-slate-400">
              {poDoc ? `PO #${poDoc.parsed_data?.document_number || 'Available'}` : 'No Purchase Order linked'}
            </p>
          </div>
        </div>

        {/* 2. Invoiced Commercial Billed */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Invoiced Total</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="space-y-0.5">
            <p className="text-xl font-mono font-extrabold text-indigo-300">
              {invoiceTotal > 0 ? `₹${invoiceTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
            </p>
            <p className="text-[11px] text-slate-400">
              {invDoc ? `Inv #${invDoc.parsed_data?.document_number || 'Available'}` : 'No Invoice linked'}
            </p>
          </div>
        </div>

        {/* 3. Settled Paid Total */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Settled / Paid</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CreditCard className="w-4 h-4" />
            </div>
          </div>
          <div className="space-y-0.5">
            <p className="text-xl font-mono font-extrabold text-emerald-400">
              {paidTotal > 0 ? `₹${paidTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '₹0.00'}
            </p>
            <p className="text-[11px] text-slate-400">
              {payDoc ? `Ref #${payDoc.parsed_data?.transaction_reference || 'Recorded'}` : 'No Payment Receipt linked'}
            </p>
          </div>
        </div>

        {/* 4. Outstanding / Shortfall */}
        <div className={`p-4 rounded-2xl border space-y-2 ${
          outstandingAmount > 0 
            ? 'bg-rose-950/20 border-rose-500/30' 
            : 'bg-slate-900/80 border-slate-800'
        }`}>
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {outstandingAmount > 0 ? 'Outstanding Shortfall' : 'Settlement Balance'}
            </span>
            <div className={`p-2 rounded-xl ${
              outstandingAmount > 0 
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            }`}>
              {outstandingAmount > 0 ? <ShieldAlert className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            </div>
          </div>
          <div className="space-y-0.5">
            <p className={`text-xl font-mono font-extrabold ${outstandingAmount > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              ₹{outstandingAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
            <p className="text-[11px] text-slate-400">
              {outstandingAmount > 0 ? 'Pending payment settlement' : 'Fully settled / Zero balance'}
            </p>
          </div>
        </div>

      </div>

      {/* Reconciliation Financial Breakdown Strip */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <span>Three-Way Financial Reconciliation Balance</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          
          {/* Check 1: PO vs Invoice */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">PO vs Invoice</span>
              {poTotal > 0 && invoiceTotal > 0 ? (
                poTotal === invoiceTotal ? (
                  <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Exact Match
                  </span>
                ) : (
                  <span className="text-[11px] font-bold text-rose-400 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Variance: ₹{Math.abs(invoiceTotal - poTotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                )
              ) : (
                <span className="text-[11px] text-slate-500">Incomplete Pair</span>
              )}
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
              <span>PO: ₹{poTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              <ArrowRight className="w-3 h-3 text-slate-600" />
              <span>Inv: ₹{invoiceTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          {/* Check 2: Delivery vs Invoice */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">Delivery vs Invoice</span>
              {deliveredValue > 0 && invoiceTotal > 0 ? (
                deliveredValue === invoiceTotal ? (
                  <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Delivered 100%
                  </span>
                ) : (
                  <span className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Goods Gap: ₹{Math.abs(invoiceTotal - deliveredValue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                )
              ) : (
                <span className="text-[11px] text-slate-500">Incomplete Pair</span>
              )}
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Delivered: ₹{deliveredValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              <ArrowRight className="w-3 h-3 text-slate-600" />
              <span>Billed: ₹{invoiceTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          {/* Check 3: Invoice vs Paid */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">Invoice vs Paid</span>
              {paidTotal >= invoiceTotal && invoiceTotal > 0 ? (
                <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Fully Settled
                </span>
              ) : paidTotal > 0 ? (
                <span className="text-[11px] font-bold text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Shortfall: ₹{(invoiceTotal - paidTotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              ) : (
                <span className="text-[11px] font-bold text-slate-400">Payment Pending</span>
              )}
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Billed: ₹{invoiceTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              <ArrowRight className="w-3 h-3 text-slate-600" />
              <span>Paid: ₹{paidTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

        </div>
      </div>

      {/* Multi-Document Line Item Reconciliation Matrix */}
      {itemReconciliationRows.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h4 className="text-sm font-bold text-slate-100">Multi-Document Line-Item Audit Matrix</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Side-by-side alignment of item quantities and unit prices across PO, Delivery Note, and Invoice
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg self-start sm:self-auto">
              {itemReconciliationRows.length} Line Items Detected
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Item Description</th>
                  <th className="py-3 px-4 text-center">PO Ordered</th>
                  <th className="py-3 px-4 text-center">Delivered</th>
                  <th className="py-3 px-4 text-center">Invoiced Qty</th>
                  <th className="py-3 px-4 text-right">Invoiced Rate</th>
                  <th className="py-3 px-4 text-right">Invoiced Total</th>
                  <th className="py-3 px-4 text-center">Line Item Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {itemReconciliationRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-sans font-medium text-slate-100 max-w-xs truncate">
                      {row.description}
                    </td>
                    <td className="py-3.5 px-4 text-center text-slate-300">
                      {row.poQty !== null ? `${row.poQty} ${row.unit}` : '—'}
                      {row.poPrice !== null && (
                        <div className="text-[10px] text-slate-500 font-sans">@ ₹{row.poPrice}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-center text-slate-300">
                      {row.dnQty !== null ? `${row.dnQty} ${row.unit}` : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-center text-indigo-300 font-bold">
                      {row.invQty !== null ? `${row.invQty} ${row.unit}` : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-200">
                      {row.invPrice !== null ? `₹${row.invPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-100 font-bold">
                      {row.invTotal !== null ? `₹${row.invTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className={`inline-flex items-center gap-1 text-[11px] font-sans font-bold px-2.5 py-0.5 rounded-full border ${row.statusColor}`}>
                        {row.status === 'MATCHED' && <CheckCircle2 className="w-3 h-3" />}
                        {row.status !== 'MATCHED' && <AlertTriangle className="w-3 h-3" />}
                        <span>{row.statusLabel}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Tax & Grand Total Sub-footer */}
          {(invoiceSubtotal > 0 || invoiceTax > 0) && (
            <div className="bg-slate-950/80 p-4 border-t border-slate-800 flex flex-wrap items-center justify-end gap-6 text-xs">
              {invoiceSubtotal > 0 && (
                <div className="text-right">
                  <span className="text-slate-400 font-sans">Taxable Subtotal: </span>
                  <span className="font-mono font-bold text-slate-200">₹{invoiceSubtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              )}
              {invoiceTax > 0 && (
                <div className="text-right">
                  <span className="text-slate-400 font-sans">GST Tax Total: </span>
                  <span className="font-mono font-bold text-indigo-300">₹{invoiceTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              )}
              {invoiceTotal > 0 && (
                <div className="text-right">
                  <span className="text-slate-400 font-sans">Invoice Grand Total: </span>
                  <span className="font-mono font-extrabold text-emerald-400">₹{invoiceTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
};
