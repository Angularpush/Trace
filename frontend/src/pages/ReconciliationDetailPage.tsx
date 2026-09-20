import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  FileText, 
  AlertTriangle, 
  Sparkles, 
  CheckCircle2,
  Bot
} from 'lucide-react';
import { api } from '../api';
import type { TransactionItem, ReconciliationSummaryReport, ReconciliationMode, DiscrepancyItem } from '../types';
import { StatusBadge } from '../components/common/Badge';
import { TransactionFlowGraph } from '../components/reconciliation/TransactionFlowGraph';
import { FinancialSummary } from '../components/reconciliation/FinancialSummary';
import { EvidenceInspector } from '../components/reconciliation/EvidenceInspector';
import { DiscrepancyCard } from '../components/reconciliation/DiscrepancyCard';
import { EvidenceViewerDrawer } from '../components/evidence/EvidenceViewerDrawer';
import { ReconciliationReportModal } from '../components/report/ReconciliationReportModal';

export const ReconciliationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [transaction, setTransaction] = useState<TransactionItem | null>(null);
  const [report, setReport] = useState<ReconciliationSummaryReport | null>(null);
  const [mode, setMode] = useState<ReconciliationMode>('HYBRID');
  const [llmProvider, setLlmProvider] = useState<string>('offline');
  const [isReconciling, setIsReconciling] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [inspectingDiscrepancy, setInspectingDiscrepancy] = useState<DiscrepancyItem | null>(null);
  const [activeTab, setActiveTab] = useState<'discrepancies' | 'inspector' | 'flow'>('discrepancies');

  const fetchTransaction = async () => {
    if (!id) return;
    try {
      const data = await api.getTransaction(id);
      setTransaction(data);
    } catch (err) {
      console.error('Failed to load transaction:', err);
    }
  };

  useEffect(() => {
    fetchTransaction();
  }, [id]);

  const handleRunReconciliation = async () => {
    if (!id) return;
    setIsReconciling(true);
    try {
      const rep = await api.runReconciliation(id, mode, llmProvider);
      setReport(rep);
      await fetchTransaction();
    } catch (err) {
      console.error('Reconciliation execution failed:', err);
    } finally {
      setIsReconciling(false);
    }
  };

  if (!transaction) {
    return (
      <div className="p-12 text-center text-slate-500 text-sm">
        Loading transaction workspace...
      </div>
    );
  }

  const discrepancies = transaction.discrepancies || [];
  const variance = discrepancies.reduce((acc, d) => acc + d.difference_amount, 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <Link 
            to="/transactions" 
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Transactions</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold text-slate-100">{transaction.transaction_ref}</h1>
            <StatusBadge status={transaction.reconciliation_status} />
            {variance > 0 && (
              <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">
                Variance: ₹{variance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            <b>Supplier:</b> {transaction.supplier_name || 'MSME Vendor'} • <b>Customer:</b> {transaction.customer_name || 'MSME Buyer'}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          
          {/* Mode Selector */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
            {(['HYBRID', 'RULE_BASED', 'AI_ONLY'] as ReconciliationMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-3 py-1.5 rounded-lg font-bold transition cursor-pointer ${
                  mode === m 
                    ? 'bg-indigo-600 text-white shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          {/* LLM Provider Selector */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1 text-xs">
            <Bot className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
              className="bg-transparent text-slate-300 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="offline" className="bg-slate-900 text-slate-200">Offline (Fast Template)</option>
              <option value="openai" className="bg-slate-900 text-slate-200">OpenAI (GPT-4o)</option>
              <option value="anthropic" className="bg-slate-900 text-slate-200">Anthropic (Claude)</option>
            </select>
          </div>

          {/* Reconcile Action Button */}
          <button
            onClick={handleRunReconciliation}
            disabled={isReconciling}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-extrabold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isReconciling ? 'animate-spin' : ''}`} />
            <span>{isReconciling ? 'Analyzing Evidence...' : 'Run Reconciliation'}</span>
          </button>

          {/* View Formal Report Button */}
          <button
            onClick={() => {
              if (report) {
                setIsReportModalOpen(true);
              } else {
                api.getReconciliationReport(transaction.id).then(r => {
                  setReport(r);
                  setIsReportModalOpen(true);
                });
              }
            }}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>Audit Report</span>
          </button>

        </div>
      </div>

      {/* Transaction Document Flow Graph (PO -> Delivery -> Invoice -> Payment) */}
      <TransactionFlowGraph documents={transaction.documents || []} />

      {/* Financial Summary & Multi-Document Reconciliation Breakdown */}
      <FinancialSummary 
        documents={transaction.documents || []} 
        discrepancies={discrepancies}
        totalAmount={transaction.total_amount}
      />

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-bold">
        <button
          onClick={() => setActiveTab('discrepancies')}
          className={`px-4 py-2 rounded-xl transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'discrepancies'
              ? 'bg-slate-800 text-indigo-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Discrepancies ({discrepancies.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('inspector')}
          className={`px-4 py-2 rounded-xl transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'inspector'
              ? 'bg-slate-800 text-indigo-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Side-by-Side Evidence Inspector</span>
        </button>
      </div>

      {/* Tab 1: Discrepancies List */}
      {activeTab === 'discrepancies' && (
        <div className="space-y-4">
          
          {/* AI Grounded Summary Alert */}
          {transaction.reconciliation_summary && (
            <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 space-y-1.5">
              <div className="flex items-center gap-1.5 text-indigo-300 font-bold text-xs">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Executive Decision Support Summary</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {transaction.reconciliation_summary}
              </p>
            </div>
          )}

          {/* Discrepancy Cards */}
          {discrepancies.length > 0 ? (
            <div className="space-y-3">
              {discrepancies.map((d) => (
                <DiscrepancyCard 
                  key={d.id} 
                  discrepancy={d} 
                  onInspect={(item) => setInspectingDiscrepancy(item)}
                />
              ))}
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl bg-emerald-500/5 border border-emerald-500/20 text-emerald-400 space-y-2">
              <CheckCircle2 className="w-10 h-10 mx-auto" />
              <p className="font-bold text-sm">Zero Discrepancies Found</p>
              <p className="text-xs text-slate-400">
                All multi-document line items, quantities, taxes, and payments match with 100% mathematical precision.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Side-by-Side Inspector */}
      {activeTab === 'inspector' && (
        <EvidenceInspector documents={transaction.documents || []} />
      )}

      {/* Interactive Evidence Viewer Drawer / Side Panel */}
      <EvidenceViewerDrawer
        isOpen={!!inspectingDiscrepancy}
        onClose={() => setInspectingDiscrepancy(null)}
        discrepancy={inspectingDiscrepancy}
      />

      {/* Formal Printable Report Modal */}
      {report && (
        <ReconciliationReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          report={report}
        />
      )}

    </div>
  );
};
