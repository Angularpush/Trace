import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  GitCompare, 
  AlertTriangle, 
  ShieldCheck, 
  ArrowUpRight, 
  Upload, 
  Sparkles, 
  Layers, 
  RefreshCw,
  TrendingDown,
  Loader2,
  FileText,
  AlertCircle,
  PieChart as PieIcon,
  BarChart3,
  DollarSign,
  CheckCircle2,
  Database,
  ArrowRight
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell, 
  PieChart, 
  Pie, 
  Legend
} from 'recharts';
import { api } from '../api';
import type { TransactionItem, DocumentItem, DiscrepancyItem } from '../types';
import { StatusBadge } from '../components/common/Badge';
import { DocumentUploadModal } from '../components/upload/DocumentUploadModal';

// Rule code human-readable mapping
const RULE_LABELS: Record<string, string> = {
  R001: 'Price Mismatch',
  PRICE_MISMATCH: 'Price Mismatch',
  R002: 'Qty Overbilled',
  QUANTITY_OVERBILLED: 'Qty Overbilled',
  R003: 'Payment Shortfall',
  PAYMENT_SHORTFALL: 'Payment Shortfall',
  R004: 'Missing Delivery',
  MISSING_DELIVERY_NOTE: 'Missing Delivery',
  R005: 'Qty Undelivered',
  QUANTITY_UNDELIVERED_BILLED: 'Qty Undelivered',
  R006: 'Duplicate Invoice',
  DUPLICATE_INVOICE: 'Duplicate Invoice',
  R007: 'Tax Calculation Error',
  TAX_CALCULATION_ERROR: 'Tax Calculation Error',
  R008: 'Advance Unrecorded',
  ADVANCE_PAYMENT_NOT_DEDUCTED: 'Advance Unrecorded',
  R009: 'Unrecorded Debit Note',
  UNRECORDED_DEBIT_NOTE: 'Unrecorded Debit Note',
  R010: 'Unauthorized Payment',
  PAYMENT_BEFORE_DELIVERY_UNAUTHORIZED: 'Unauthorized Payment'
};

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#f43f5e',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#3b82f6'
};

const STATUS_COLORS: Record<string, string> = {
  RECONCILED: '#10b981',
  DISCREPANCY_FOUND: '#f43f5e',
  MINOR_VARIANCE: '#f59e0b',
  INCOMPLETE: '#eab308',
  PENDING: '#64748b'
};

const STATUS_LABELS: Record<string, string> = {
  RECONCILED: 'Reconciled',
  DISCREPANCY_FOUND: 'Discrepancy Detected',
  MINOR_VARIANCE: 'Minor Variance',
  INCOMPLETE: 'Incomplete Docs',
  PENDING: 'Pending Audit'
};

// Custom Tooltip Component for Charts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-2xl text-xs space-y-1">
        {label && <p className="font-bold text-slate-200 border-b border-slate-800 pb-1">{label}</p>}
        {payload.map((p: any, idx: number) => (
          <p key={idx} className="flex items-center gap-2" style={{ color: p.color || p.fill || '#818cf8' }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color || p.fill || '#818cf8' }} />
            <span>{p.name}: <b>{typeof p.value === 'number' && p.unit === '₹' ? `₹${p.value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : p.value}</b></span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [txns, docs] = await Promise.all([
        api.listTransactions(),
        api.listDocuments()
      ]);
      setTransactions(txns);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    setSeedMessage(null);
    try {
      await api.seedDemo();
      setSeedMessage('Demo dataset (TXN-001 Clean Match & TXN-002 Multi-Discrepancy) loaded successfully!');
      await fetchData();
    } catch (err: any) {
      setSeedMessage(err?.response?.data?.detail || 'Failed to seed demo data.');
    } finally {
      setIsSeeding(false);
    }
  };

  const handleAutoLink = async () => {
    try {
      const updated = await api.autoLinkTransactions();
      setTransactions(updated);
    } catch (err) {
      console.error('Auto link failed:', err);
    }
  };

  // Metrics Computations
  const allDiscrepancies: DiscrepancyItem[] = transactions.flatMap(t => t.discrepancies || []);
  const totalTransactionsCount = transactions.length;
  const reconciledCount = transactions.filter(t => t.reconciliation_status === 'RECONCILED').length;
  const totalDiscrepanciesCount = allDiscrepancies.length;
  const criticalDiscrepanciesCount = allDiscrepancies.filter(d => d.severity === 'CRITICAL').length;
  const highDiscrepanciesCount = allDiscrepancies.filter(d => d.severity === 'HIGH').length;

  const needsReviewCount = transactions.filter(t => 
    t.reconciliation_status === 'DISCREPANCY_FOUND' || 
    t.reconciliation_status === 'INCOMPLETE' || 
    t.reconciliation_status === 'MINOR_VARIANCE'
  ).length;

  const paymentShortfallDiscrepancies = allDiscrepancies.filter(d => 
    d.rule_code === 'R003' || d.discrepancy_type === 'PAYMENT_SHORTFALL'
  );
  
  const outstandingPaymentsTotal = paymentShortfallDiscrepancies.reduce(
    (acc, d) => acc + (d.difference_amount || 0), 0
  );

  const transactionsWithShortfall = transactions.filter(t => 
    t.discrepancies?.some(d => d.rule_code === 'R003' || d.discrepancy_type === 'PAYMENT_SHORTFALL')
  ).length;

  // Chart 1: Discrepancies by Type Data
  const discrepancyTypeCounts: Record<string, number> = {};
  allDiscrepancies.forEach(d => {
    const label = RULE_LABELS[d.rule_code] || RULE_LABELS[d.discrepancy_type] || d.discrepancy_type || 'Other';
    discrepancyTypeCounts[label] = (discrepancyTypeCounts[label] || 0) + 1;
  });

  const discrepanciesByTypeData = Object.entries(discrepancyTypeCounts).map(([type, count]) => ({
    name: type,
    count: count
  }));

  // Chart 2: Severity Distribution Data
  const severityCounts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  allDiscrepancies.forEach(d => {
    const sev = (d.severity || 'LOW').toUpperCase();
    if (severityCounts[sev] !== undefined) {
      severityCounts[sev]++;
    }
  });

  const severityDistributionData = Object.entries(severityCounts)
    .filter(([_, count]) => count > 0)
    .map(([sev, count]) => ({
      name: sev,
      value: count,
      color: SEVERITY_COLORS[sev] || '#3b82f6'
    }));

  // Chart 3: Status Distribution Data
  const statusCounts: Record<string, number> = {
    RECONCILED: 0,
    DISCREPANCY_FOUND: 0,
    MINOR_VARIANCE: 0,
    INCOMPLETE: 0,
    PENDING: 0
  };
  transactions.forEach(t => {
    const st = (t.reconciliation_status || 'PENDING').toUpperCase();
    if (statusCounts[st] !== undefined) {
      statusCounts[st]++;
    } else {
      statusCounts['PENDING']++;
    }
  });

  const statusDistributionData = Object.entries(statusCounts)
    .filter(([_, count]) => count > 0)
    .map(([st, count]) => ({
      name: STATUS_LABELS[st] || st,
      rawStatus: st,
      value: count,
      color: STATUS_COLORS[st] || '#64748b'
    }));

  // Chart 4: Outstanding Payments Data
  const outstandingPaymentsData = transactions.map(t => {
    const shortfall = t.discrepancies
      ?.filter(d => d.rule_code === 'R003' || d.discrepancy_type === 'PAYMENT_SHORTFALL')
      .reduce((acc, d) => acc + (d.difference_amount || 0), 0) || 0;

    return {
      name: t.transaction_ref || t.id.substring(0, 8),
      supplier: t.supplier_name || 'Vendor',
      invoicedAmount: Number(t.total_amount) || 0,
      outstandingShortfall: shortfall,
      reconciledPaid: Math.max(0, (Number(t.total_amount) || 0) - shortfall)
    };
  });

  const hasData = transactions.length > 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Presentation Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="space-y-2.5 z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Document-Level MSME Transaction Reconciliation System</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            TRACE Intelligent Audit Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Multi-document financial discrepancy detection uniting supervised document classification, graph-based transaction clustering, and 10 deterministic <code className="text-indigo-300">Decimal</code> verification rules.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 z-10 shrink-0">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Documents</span>
          </button>
          <button
            onClick={handleSeedDemo}
            disabled={isSeeding}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/30 text-emerald-300 text-xs font-bold transition cursor-pointer disabled:opacity-50"
          >
            {isSeeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4 text-emerald-400" />}
            <span>Load Demo Dataset</span>
          </button>
          <button
            onClick={handleAutoLink}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Auto-Link TXNs</span>
          </button>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {seedMessage && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{seedMessage}</span>
          </div>
          <button onClick={() => setSeedMessage(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* 5 KEY METRICS CARDS (Interactive Quick Filters)              */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        
        {/* Card 1: Total Transactions */}
        <div 
          onClick={() => navigate('/transactions')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/transactions')}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-indigo-500/50 hover:bg-slate-900/90 hover:scale-[1.02] active:scale-[0.99] transition-all duration-200 cursor-pointer group shadow-sm hover:shadow-indigo-500/10"
          title="Click to view all transactions"
        >
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider group-hover:text-indigo-300 transition">Total Transactions</span>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/20 transition">
                <Layers className="w-4 h-4" />
              </div>
            </div>
          </div>
          <p className="text-2xl font-black text-slate-100 font-mono group-hover:text-indigo-200 transition">{totalTransactionsCount}</p>
          <p className="text-[11px] text-slate-500 group-hover:text-slate-400 transition">{documents.length} source documents linked</p>
        </div>

        {/* Card 2: Reconciled */}
        <div 
          onClick={() => navigate('/transactions?status=RECONCILED')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/transactions?status=RECONCILED')}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-emerald-500/50 hover:bg-slate-900/90 hover:scale-[1.02] active:scale-[0.99] transition-all duration-200 cursor-pointer group shadow-sm hover:shadow-emerald-500/10"
          title="Click to view reconciled transactions"
        >
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider group-hover:text-emerald-300 transition">Reconciled</span>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500/20 transition">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-black text-emerald-400 font-mono">{reconciledCount}</p>
            {totalTransactionsCount > 0 && (
              <span className="text-xs font-bold text-emerald-500/90 font-mono">
                ({Math.round((reconciledCount / totalTransactionsCount) * 100)}%)
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 group-hover:text-slate-400 transition">100% 4-way matching consistency</p>
        </div>

        {/* Card 3: Discrepancies */}
        <div 
          onClick={() => navigate('/transactions?filter=discrepancies')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/transactions?filter=discrepancies')}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-rose-500/50 hover:bg-slate-900/90 hover:scale-[1.02] active:scale-[0.99] transition-all duration-200 cursor-pointer group shadow-sm hover:shadow-rose-500/10"
          title="Click to view transactions with discrepancies"
        >
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider group-hover:text-rose-300 transition">Discrepancies</span>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400 group-hover:bg-rose-500/20 transition">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-black text-rose-400 font-mono">{totalDiscrepanciesCount}</p>
            {criticalDiscrepanciesCount > 0 && (
              <span className="text-[11px] font-bold text-red-400 font-mono">
                ({criticalDiscrepanciesCount} Critical)
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 group-hover:text-slate-400 transition">{highDiscrepanciesCount} high severity flags</p>
        </div>

        {/* Card 4: Needs Review */}
        <div 
          onClick={() => navigate('/transactions?filter=needs_review')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/transactions?filter=needs_review')}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-amber-500/50 hover:bg-slate-900/90 hover:scale-[1.02] active:scale-[0.99] transition-all duration-200 cursor-pointer group shadow-sm hover:shadow-amber-500/10"
          title="Click to view transactions needing review"
        >
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider group-hover:text-amber-300 transition">Needs Review</span>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 group-hover:bg-amber-500/20 transition">
                <AlertCircle className="w-4 h-4" />
              </div>
            </div>
          </div>
          <p className="text-2xl font-black text-amber-400 font-mono">{needsReviewCount}</p>
          <p className="text-[11px] text-slate-500 group-hover:text-slate-400 transition">Requires auditor decision</p>
        </div>

        {/* Card 5: Outstanding Payments */}
        <div 
          onClick={() => navigate('/transactions?filter=outstanding')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/transactions?filter=outstanding')}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-rose-500/50 hover:bg-slate-900/90 hover:scale-[1.02] active:scale-[0.99] transition-all duration-200 cursor-pointer group shadow-sm hover:shadow-rose-500/10"
          title="Click to view transactions with outstanding shortfalls"
        >
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider group-hover:text-rose-300 transition">Outstanding Payments</span>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400 group-hover:bg-rose-500/20 transition">
                <TrendingDown className="w-4 h-4" />
              </div>
            </div>
          </div>
          <p className="text-xl font-black text-rose-400 font-mono truncate">
            ₹{outstandingPaymentsTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
          <p className="text-[11px] text-slate-500 group-hover:text-slate-400 transition">{transactionsWithShortfall} shortfalls detected</p>
        </div>

      </div>

      {/* ------------------------------------------------------------- */}
      {/* 4 CHARTS GRID (RECHARTS)                                      */}
      {/* ------------------------------------------------------------- */}
      {isLoading ? (
        <div className="p-16 text-center border border-slate-800 rounded-3xl bg-slate-900/40 space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Computing real-time multi-document metrics...</p>
        </div>
      ) : hasData ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Chart 1: Discrepancies by Type */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  <span>Discrepancies by Type</span>
                </h3>
                <p className="text-[11px] text-slate-400">Categorical breakdown of deterministic rule violations</p>
              </div>
              <span className="text-xs font-mono font-bold text-slate-400">{allDiscrepancies.length} Total</span>
            </div>

            {discrepanciesByTypeData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={discrepanciesByTypeData} 
                    margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                  >
                    <XAxis 
                      dataKey="name" 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      interval={0}
                      angle={-20}
                      textAnchor="end"
                    />
                    <YAxis 
                      allowDecimals={false} 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" name="Discrepancies" radius={[6, 6, 0, 0]}>
                      {discrepanciesByTypeData.map((_, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={['#6366f1', '#ec4899', '#f43f5e', '#f59e0b', '#06b6d4', '#8b5cf6'][index % 6]} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2 border border-dashed border-slate-800 rounded-2xl">
                <ShieldCheck className="w-8 h-8 text-emerald-500/40" />
                <p>No discrepancies detected in active transactions.</p>
              </div>
            )}
          </div>

          {/* Chart 2: Severity Distribution */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <PieIcon className="w-4 h-4 text-rose-400" />
                  <span>Severity Distribution</span>
                </h3>
                <p className="text-[11px] text-slate-400">Risk rating of flagged variances & audit discrepancies</p>
              </div>
            </div>

            {severityDistributionData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityDistributionData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={4}
                    >
                      {severityDistributionData.map((entry, index) => (
                        <Cell key={`sev-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36}
                      formatter={(val: string) => <span className="text-xs text-slate-300 font-semibold">{val}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2 border border-dashed border-slate-800 rounded-2xl">
                <ShieldCheck className="w-8 h-8 text-emerald-500/40" />
                <p>Zero risk flags present in current document clusters.</p>
              </div>
            )}
          </div>

          {/* Chart 3: Reconciliation Status Distribution */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <GitCompare className="w-4 h-4 text-emerald-400" />
                  <span>Reconciliation Status</span>
                </h3>
                <p className="text-[11px] text-slate-400">Current audit state across all multi-document transactions</p>
              </div>
            </div>

            {statusDistributionData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusDistributionData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={4}
                    >
                      {statusDistributionData.map((entry, index) => (
                        <Cell key={`status-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36}
                      formatter={(val: string) => <span className="text-xs text-slate-300 font-semibold">{val}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2 border border-dashed border-slate-800 rounded-2xl">
                <Layers className="w-8 h-8 text-slate-600" />
                <p>No transaction clusters available to evaluate.</p>
              </div>
            )}
          </div>

          {/* Chart 4: Outstanding Payments by Transaction */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  <span>Outstanding Payments by Transaction</span>
                </h3>
                <p className="text-[11px] text-slate-400">Total invoiced value vs identified unpaid shortfall (INR)</p>
              </div>
            </div>

            {outstandingPaymentsData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={outstandingPaymentsData}
                    margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
                  >
                    <XAxis 
                      dataKey="name" 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                    />
                    <YAxis 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36}
                      formatter={(val: string) => <span className="text-xs text-slate-300 font-semibold">{val}</span>}
                    />
                    <Bar dataKey="invoicedAmount" name="Invoiced Amount" unit="₹" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="outstandingShortfall" name="Outstanding Shortfall" unit="₹" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2 border border-dashed border-slate-800 rounded-2xl">
                <DollarSign className="w-8 h-8 text-slate-600" />
                <p>No transaction payment data found.</p>
              </div>
            )}
          </div>

        </div>
      ) : (
        /* ------------------------------------------------------------- */
        /* CLEAN EMPTY STATE                                             */
        /* ------------------------------------------------------------- */
        <div className="p-12 sm:p-16 rounded-3xl border border-dashed border-slate-800 bg-slate-900/30 text-center space-y-5 animate-in fade-in">
          <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400">
            <Layers className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-slate-200">No Transactions Ingested Yet</h3>
            <p className="text-xs text-slate-400">
              TRACE requires multi-document bundles (Purchase Orders, Tax Invoices, Delivery Challans, and Payment Receipts) to perform automated graph linking and deterministic financial reconciliation.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/20 transition cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Document Batch</span>
            </button>
            <button
              onClick={handleSeedDemo}
              disabled={isSeeding}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition cursor-pointer"
            >
              {isSeeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4 text-emerald-400" />}
              <span>Load Academic Demo Dataset</span>
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* RECENT TRANSACTIONS TABLE                                     */}
      {/* ------------------------------------------------------------- */}
      {hasData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Recent Reconciled Transactions</span>
              </h3>
              <p className="text-xs text-slate-400">Multi-document business transactions with cross-referencing audit trails</p>
            </div>
            <Link 
              to="/transactions" 
              className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition"
            >
              <span>View All ({transactions.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="border border-slate-800 rounded-3xl bg-slate-900/60 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
                    <th className="py-3.5 px-5">Transaction Ref</th>
                    <th className="py-3.5 px-4">Supplier & Customer</th>
                    <th className="py-3.5 px-4">Docs Linked</th>
                    <th className="py-3.5 px-4">Total Amount</th>
                    <th className="py-3.5 px-4">Audit Status</th>
                    <th className="py-3.5 px-4">Discrepancies</th>
                    <th className="py-3.5 px-5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {transactions.slice(0, 6).map((txn) => {
                    const discCount = txn.discrepancies?.length || 0;
                    const hasDiscrepancy = discCount > 0;

                    return (
                      <tr key={txn.id} className="hover:bg-slate-800/40 transition">
                        
                        <td className="py-3.5 px-5 font-mono font-bold text-indigo-300">
                          {txn.transaction_ref}
                        </td>

                        <td className="py-3.5 px-4 text-slate-200">
                          <p className="font-semibold text-slate-100">{txn.supplier_name || 'Generic Vendor'}</p>
                          <p className="text-[10px] text-slate-400">{txn.customer_name || 'MSME Buyer'}</p>
                        </td>

                        <td className="py-3.5 px-4 text-slate-300 font-mono text-[11px]">
                          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                            {txn.documents?.length || 0} Docs
                          </span>
                        </td>

                        <td className="py-3.5 px-4 font-mono font-bold text-slate-200">
                          ₹{Number(txn.total_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>

                        <td className="py-3.5 px-4">
                          <StatusBadge status={txn.reconciliation_status} />
                        </td>

                        <td className="py-3.5 px-4">
                          {hasDiscrepancy ? (
                            <span className="inline-flex items-center gap-1.5 text-rose-400 font-bold font-mono text-[11px]">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              <span>{discCount} Flag{discCount > 1 ? 's' : ''}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-emerald-400 font-bold text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Clean Match</span>
                            </span>
                          )}
                        </td>

                        <td className="py-3.5 px-5 text-right">
                          <Link
                            to={`/transactions/${txn.id}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/15 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-bold border border-indigo-500/30 transition cursor-pointer"
                          >
                            <span>Inspect Audit</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>

                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Document Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => {
          fetchData();
        }}
        onNavigateToTransaction={(txnId) => {
          navigate(`/transactions/${txnId}`);
        }}
      />

    </div>
  );
};
