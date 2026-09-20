import React from 'react';
import type { DocumentType, SeverityLevel, TransactionStatus } from '../../types';

interface DocTypeBadgeProps {
  type: DocumentType | string;
  confidence?: number;
  className?: string;
}

export const DocTypeBadge: React.FC<DocTypeBadgeProps> = ({ type, confidence, className = '' }) => {
  const styles: Record<string, { bg: string; text: string; border: string; label: string }> = {
    PURCHASE_ORDER: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30', label: 'Purchase Order' },
    INVOICE: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'Tax Invoice' },
    DELIVERY_NOTE: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', label: 'Delivery Note' },
    PAYMENT_RECEIPT: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30', label: 'Payment Receipt' },
    QUOTATION: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30', label: 'Quotation' },
    CREDIT_NOTE: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30', label: 'Credit Note' },
    DEBIT_NOTE: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', label: 'Debit Note' },
    UNKNOWN: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30', label: 'Unknown' },
  };

  const style = styles[type] || styles.UNKNOWN;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${style.bg} ${style.text} ${style.border} ${className}`}>
      <span>{style.label}</span>
      {confidence !== undefined && (
        <span className="opacity-75 text-[10px] font-mono">({Math.round(confidence * 100)}%)</span>
      )}
    </span>
  );
};

interface SeverityBadgeProps {
  severity: SeverityLevel | string;
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, className = '' }) => {
  const styles: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    CRITICAL: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30', dot: 'bg-red-400' },
    HIGH: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30', dot: 'bg-orange-400' },
    MEDIUM: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', dot: 'bg-amber-400' },
    LOW: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', dot: 'bg-blue-400' },
  };

  const style = styles[severity.toUpperCase()] || styles.LOW;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${style.bg} ${style.text} ${style.border} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      <span>{severity.toUpperCase()}</span>
    </span>
  );
};

interface StatusBadgeProps {
  status: TransactionStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const styles: Record<string, { bg: string; text: string; border: string; label: string }> = {
    RECONCILED: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'Reconciled (100% Match)' },
    DISCREPANCY_FOUND: { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30', label: 'Discrepancy Detected' },
    MINOR_VARIANCE: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', label: 'Minor Variance' },
    INCOMPLETE: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/30', label: 'Missing Documents' },
    PENDING: { bg: 'bg-slate-500/15', text: 'text-slate-400', border: 'border-slate-500/30', label: 'Pending Audit' },
  };

  const style = styles[status] || styles.PENDING;

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${style.bg} ${style.text} ${style.border} ${className}`}>
      {style.label}
    </span>
  );
};

interface ProcessStatusBadgeProps {
  status: string;
  className?: string;
}

export const ProcessStatusBadge: React.FC<ProcessStatusBadgeProps> = ({ status, className = '' }) => {
  const styles: Record<string, { bg: string; text: string; border: string; dot: string; label: string }> = {
    UPLOADED: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', dot: 'bg-blue-400', label: 'UPLOADED' },
    PROCESSING: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', dot: 'bg-amber-400 animate-ping', label: 'PROCESSING' },
    EXTRACTED: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', border: 'border-cyan-500/30', dot: 'bg-cyan-400', label: 'EXTRACTED' },
    CLASSIFIED: { bg: 'bg-purple-500/15', text: 'text-purple-400', border: 'border-purple-500/30', dot: 'bg-purple-400', label: 'CLASSIFIED' },
    MATCHED: { bg: 'bg-indigo-500/15', text: 'text-indigo-400', border: 'border-indigo-500/30', dot: 'bg-indigo-400', label: 'MATCHED' },
    RECONCILED: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', dot: 'bg-emerald-400', label: 'RECONCILED' },
    FAILED: { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30', dot: 'bg-rose-400', label: 'FAILED' },
    IDLE: { bg: 'bg-slate-500/15', text: 'text-slate-400', border: 'border-slate-500/30', dot: 'bg-slate-400', label: 'IDLE' },
  };

  const style = styles[status.toUpperCase()] || styles.IDLE;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-bold font-mono border ${style.bg} ${style.text} ${style.border} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      <span>{style.label}</span>
    </span>
  );
};
