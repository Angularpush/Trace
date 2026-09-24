import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  FileText, 
  AlertTriangle, 
  Sparkles, 
  CheckCircle2,
  Bot,
  GitCompare,
  DollarSign,
  Scale,
  ShieldCheck,
  Layers,
  FileWarning
} from 'lucide-react';
import { api } from '../api';
import type { 
  TransactionItem, 
  ReconciliationSummaryReport, 
  DiscrepancyItem,
  ComparisonResult,
  TransactionGraph,
  DisputeNoticeResponse
} from '../types';
import { StatusBadge } from '../components/common/Badge';
import { TransactionFlowGraph } from '../components/reconciliation/TransactionFlowGraph';
import { FinancialSummary } from '../components/reconciliation/FinancialSummary';
import { DiscrepancyCard } from '../components/reconciliation/DiscrepancyCard';
import { EvidenceViewerDrawer } from '../components/evidence/EvidenceViewerDrawer';
import { ReconciliationReportModal } from '../components/report/ReconciliationReportModal';
import { DisputeNoticeModal } from '../components/report/DisputeNoticeModal';

export const ReconciliationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [transaction, setTransaction] = useState<TransactionItem | null>(null);
  const [graphData, setGraphData] = useState<TransactionGraph | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [report, setReport] = useState<ReconciliationSummaryReport | null>(null);
  const [disputeNotice, setDisputeNotice] = useState<DisputeNoticeResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isDisputeModalOpen, setIsDisputeModalOpen] = useState(false);
  const [isLoadingDispute, setIsLoadingDispute] = useState(false);

  const handleOpenReport = async () => {
    if (!report && id) {
      try {
        const rep = await api.getReconciliationReport(id);
        setReport(rep);
      } catch (err) {
        console.error('Failed to load report:', err);
      }
    }
    setIsReportModalOpen(true);
  };

  const handleOpenDisputeNotice = async () => {
    if (!id) return;
    setIsLoadingDispute(true);
    setIsDisputeModalOpen(true);
    try {
      const notice = await api.getDisputeNotice(id);
      setDisputeNotice(notice);
    } catch (err) {
      console.error('Failed to load dispute notice:', err);
    } finally {
      setIsLoadingDispute(false);
    }
  };
  const [inspectingDiscrepancy, setInspectingDiscrepancy] = useState<DiscrepancyItem | null>(null);
  const [activeTab, setActiveTab] = useState<'compare' | 'discrepancies' | 'flow' | 'financial'>('compare');

  const fetchTransaction = async () => {
    if (!id) return;
    try {
      const [data, graph] = await Promise.all([
        api.getTransaction(id),
        api.getTransactionGraph(id).catch(() => null)
      ]);
      setTransaction(data);
      if (graph) setGraphData(graph);
    } catch (err) {
      console.error('Failed to load transaction:', err);
    }
  };

  useEffect(() => {
    fetchTransaction();
  }, [id]);

  const handleRunComparison = async () => {
    if (!id) return;
    setIsComparing(true);
    try {
      const comp = await api.compareApproaches(id);
      setComparisonResult(comp);
      await fetchTransaction();
      setActiveTab('compare');
    } catch (err) {
      console.error('Comparison execution failed:', err);
    } finally {
      setIsComparing(false);
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
  const variance = discrepancies.reduce((acc, d) => acc + (d.difference_amount || 0), 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* Top Header & Actions */}
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
            <h1 className="text-2xl font-extrabold text-slate-100">{transaction.transaction_reference || transaction.transaction_ref}</h1>
            <StatusBadge status={transaction.status || transaction.reconciliation_status} />
            {variance > 0 && (
              <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">
                Variance: ₹{variance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            <b>Supplier:</b> {transaction.supplier || transaction.supplier_name || 'MSME Vendor'} &bull; <b>Customer:</b> {transaction.customer || transaction.customer_name || 'MSME Buyer'}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleRunComparison}
            disabled={isComparing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/30 cursor-pointer disabled:opacity-50"
          >
            <GitCompare className={`w-4 h-4 ${isComparing ? 'animate-spin' : ''}`} />
            <span>{isComparing ? 'Comparing 3 Approaches...' : 'Run 3-Way Comparison'}</span>
          </button>

          <button
            onClick={handleOpenDisputeNotice}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              discrepancies.length > 0
                ? 'bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/40 text-rose-300 shadow-sm shadow-rose-950/50'
                : 'bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300'
            }`}
          >
            <FileWarning className="w-4 h-4 text-rose-400" />
            <span>Dispute Notice</span>
          </button>

          <button
            onClick={handleOpenReport}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer"
          >
            <FileText className="w-4 h-4" />
            <span>Audit Report</span>
          </button>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('compare')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'compare' 
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>3-Way Engine Comparator</span>
        </button>

        <button
          onClick={() => setActiveTab('discrepancies')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'discrepancies' 
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Discrepancies ({discrepancies.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('flow')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'flow' 
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Document Linking Graph</span>
        </button>

        <button
          onClick={() => setActiveTab('financial')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'financial' 
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <DollarSign className="w-3.5 h-3.5" />
          <span>Financial Summary</span>
        </button>
      </div>

      {/* Tab 1: 3-Way Engine Comparator View */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {comparisonResult ? (
            <div className="space-y-6">
              {/* Comparison Header Summary Banner */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">3-Way Agreement Analysis</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      Consensus: {(comparisonResult.agreement_score * 100).toFixed(0)}% Overlap
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {comparisonResult.explanation_summary}
                  </p>
                </div>
                
                <div className="flex items-center gap-3 self-start md:self-auto shrink-0">
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400">Consensus Findings</p>
                    <p className="text-lg font-black text-emerald-400 font-mono">{comparisonResult.consensus_discrepancies.length}</p>
                  </div>
                  <div className="h-8 w-px bg-slate-800" />
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400">Conflicts / Unique</p>
                    <p className="text-lg font-black text-amber-400 font-mono">{comparisonResult.conflicting_discrepancies.length}</p>
                  </div>
                </div>
              </div>

              {/* Side-by-Side 3 Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                
                {/* Approach 1: RULE_BASED */}
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-blue-400" />
                      <h3 className="text-sm font-bold text-slate-100">1. RULE-BASED</h3>
                    </div>
                    <span className="text-[10px] font-bold text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                      Deterministic
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">Execution Time</span>
                      <p className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                        {comparisonResult.rule_based_run?.execution_time_ms.toFixed(2)} ms
                      </p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">API Cost</span>
                      <p className="text-sm font-bold font-mono text-emerald-400 mt-0.5">$0.0000</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Findings ({comparisonResult.rule_based_run?.findings.length || 0})
                    </h4>
                    {comparisonResult.rule_based_run?.findings.length === 0 ? (
                      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>Reconciled. No rule violations.</span>
                      </div>
                    ) : (
                      comparisonResult.rule_based_run?.findings.map((f, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-200">{f.discrepancy_type}</span>
                            <span className="text-[10px] text-blue-400 font-mono">rule</span>
                          </div>
                          <p className="text-slate-400 text-[11px]">{f.explanation}</p>
                          {f.difference_value && (
                            <p className="text-rose-400 font-mono text-[10px] font-bold">{f.difference_value}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Approach 2: AI_LLM */}
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-purple-500/30 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Bot className="w-4 h-4 text-purple-400" />
                      <h3 className="text-sm font-bold text-slate-100">2. AI / LLM</h3>
                    </div>
                    <span className="text-[10px] font-bold text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                      Reasoning
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">Execution Time</span>
                      <p className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                        {comparisonResult.ai_llm_run?.execution_time_ms.toFixed(2)} ms
                      </p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">Token Cost</span>
                      <p className="text-sm font-bold font-mono text-purple-300 mt-0.5">
                        ${comparisonResult.ai_llm_run?.cost_usd.toFixed(5)}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Findings ({comparisonResult.ai_llm_run?.findings.length || 0})
                    </h4>
                    {comparisonResult.ai_llm_run?.findings.length === 0 ? (
                      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>Reconciled. No discrepancies identified.</span>
                      </div>
                    ) : (
                      comparisonResult.ai_llm_run?.findings.map((f, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-200">{f.discrepancy_type}</span>
                            <span className="text-[10px] text-purple-400 font-mono">llm</span>
                          </div>
                          <p className="text-slate-400 text-[11px]">{f.explanation}</p>
                          {f.difference_value && (
                            <p className="text-rose-400 font-mono text-[10px] font-bold">{f.difference_value}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Approach 3: HYBRID */}
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-emerald-500/30 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <h3 className="text-sm font-bold text-slate-100">3. HYBRID</h3>
                    </div>
                    <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Rules + Embeddings + LLM
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">Execution Time</span>
                      <p className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                        {comparisonResult.hybrid_run?.execution_time_ms.toFixed(2)} ms
                      </p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400">Total Cost</span>
                      <p className="text-sm font-bold font-mono text-emerald-300 mt-0.5">
                        ${comparisonResult.hybrid_run?.cost_usd.toFixed(5)}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Findings ({comparisonResult.hybrid_run?.findings.length || 0})
                    </h4>
                    {comparisonResult.hybrid_run?.findings.length === 0 ? (
                      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>Reconciled. Complete multi-signal consistency.</span>
                      </div>
                    ) : (
                      comparisonResult.hybrid_run?.findings.map((f, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-200">{f.discrepancy_type}</span>
                            <span className="text-[10px] text-emerald-400 font-mono">{f.provenance}</span>
                          </div>
                          <p className="text-slate-400 text-[11px]">{f.explanation}</p>
                          {f.difference_value && (
                            <p className="text-rose-400 font-mono text-[10px] font-bold">{f.difference_value}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800 space-y-4">
              <Scale className="w-12 h-12 text-indigo-400 mx-auto opacity-70" />
              <div className="max-w-md mx-auto space-y-1">
                <h3 className="text-base font-bold text-slate-100">Ready for 3-Way Comparative Evaluation</h3>
                <p className="text-xs text-slate-400">
                  Run the Rule-Based, AI/LLM, and Hybrid reconciliation engines against this transaction to evaluate findings alignment, latency, and cost.
                </p>
              </div>
              <button
                onClick={handleRunComparison}
                disabled={isComparing}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-indigo-600/30 cursor-pointer disabled:opacity-50"
              >
                {isComparing ? 'Running Comparator...' : 'Execute 3-Way Comparison'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Discrepancies Detailed View */}
      {activeTab === 'discrepancies' && (
        <div className="space-y-4">
          {discrepancies.length === 0 ? (
            <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800 text-slate-400 space-y-2">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              <p className="text-sm font-bold text-slate-200">No Discrepancies Detected</p>
              <p className="text-xs text-slate-500">Transaction matches with full financial and document consistency.</p>
            </div>
          ) : (
            discrepancies.map(disc => (
              <DiscrepancyCard
                key={disc.id}
                discrepancy={disc}
                onInspect={(d) => setInspectingDiscrepancy(d)}
              />
            ))
          )}
        </div>
      )}

      {/* Tab 3: Document Linking Graph & Flow */}
      {activeTab === 'flow' && (
        <TransactionFlowGraph 
          documents={transaction.documents || []} 
          edges={graphData?.edges || []} 
        />
      )}

      {/* Tab 4: Financial Summary */}
      {activeTab === 'financial' && (
        <FinancialSummary 
          documents={transaction.documents || []}
          discrepancies={discrepancies}
          totalAmount={transaction.total_amount}
        />
      )}

      {/* Evidence Viewer Drawer */}
      {inspectingDiscrepancy && (
        <EvidenceViewerDrawer
          isOpen={!!inspectingDiscrepancy}
          discrepancy={inspectingDiscrepancy}
          onClose={() => setInspectingDiscrepancy(null)}
        />
      )}

      {/* Audit Report Modal */}
      {isReportModalOpen && report && (
        <ReconciliationReportModal
          isOpen={isReportModalOpen}
          report={report}
          onClose={() => setIsReportModalOpen(false)}
        />
      )}

      {/* Dispute Notice Modal */}
      <DisputeNoticeModal
        isOpen={isDisputeModalOpen}
        onClose={() => setIsDisputeModalOpen(false)}
        disputeNotice={disputeNotice}
        isLoading={isLoadingDispute}
      />

    </div>
  );
};
