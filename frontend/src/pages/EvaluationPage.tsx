import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Loader2, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  BarChart3, 
  Table, 
  Cpu, 
  Activity,
  FileCheck
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { api } from '../api';
import type { BenchmarkResponse, ClassifierMetricsResponse } from '../types';

export const EvaluationPage: React.FC = () => {
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [classifierMetrics, setClassifierMetrics] = useState<ClassifierMetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load existing benchmark results on mount if already evaluated
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      try {
        const [latestBm, cm] = await Promise.all([
          api.getLatestEvaluation().catch(() => null),
          api.getClassifierMetrics().catch(() => null)
        ]);
        if (latestBm) {
          setBenchmark(latestBm);
          setStatusMessage(`Evaluation loaded (Recorded at ${new Date(latestBm.evaluated_at).toLocaleTimeString()})`);
        }
        if (cm) {
          setClassifierMetrics(cm);
        }
      } catch (err: any) {
        console.error('Failed to load initial evaluation state:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    setErrorMessage(null);
    setStatusMessage('Executing multi-scenario reconciliation benchmark across RULE_BASED, AI_ONLY, and HYBRID models...');
    try {
      const startTime = performance.now();
      const results = await api.runEvaluation();
      const durationMs = Math.round(performance.now() - startTime);
      setBenchmark(results);
      setStatusMessage(`Evaluation completed successfully in ${durationMs} ms (${results.total_test_cases} test cases evaluated).`);
    } catch (err: any) {
      console.error('Evaluation execution failed:', err);
      const msg = err.response?.data?.detail || err.message || 'Evaluation run failed. Please check backend service.';
      setErrorMessage(msg);
      setStatusMessage(null);
    } finally {
      setIsRunning(false);
    }
  };

  // Prepare chart data for all 5 metrics across the 3 modes
  const chartData = benchmark ? [
    {
      metric: 'Precision',
      RULE_BASED: Number((benchmark.modes.RULE_BASED.precision * 100).toFixed(1)),
      AI_ONLY: Number((benchmark.modes.AI_ONLY.precision * 100).toFixed(1)),
      HYBRID: Number((benchmark.modes.HYBRID.precision * 100).toFixed(1)),
    },
    {
      metric: 'Recall',
      RULE_BASED: Number((benchmark.modes.RULE_BASED.recall * 100).toFixed(1)),
      AI_ONLY: Number((benchmark.modes.AI_ONLY.recall * 100).toFixed(1)),
      HYBRID: Number((benchmark.modes.HYBRID.recall * 100).toFixed(1)),
    },
    {
      metric: 'F1',
      RULE_BASED: Number((benchmark.modes.RULE_BASED.f1_score * 100).toFixed(1)),
      AI_ONLY: Number((benchmark.modes.AI_ONLY.f1_score * 100).toFixed(1)),
      HYBRID: Number((benchmark.modes.HYBRID.f1_score * 100).toFixed(1)),
    },
    {
      metric: 'Reconciliation Accuracy',
      RULE_BASED: Number((benchmark.modes.RULE_BASED.reconciliation_accuracy * 100).toFixed(1)),
      AI_ONLY: Number((benchmark.modes.AI_ONLY.reconciliation_accuracy * 100).toFixed(1)),
      HYBRID: Number((benchmark.modes.HYBRID.reconciliation_accuracy * 100).toFixed(1)),
    },
    {
      metric: 'Evidence Accuracy',
      RULE_BASED: Number((benchmark.modes.RULE_BASED.evidence_accuracy * 100).toFixed(1)),
      AI_ONLY: Number((benchmark.modes.AI_ONLY.evidence_accuracy * 100).toFixed(1)),
      HYBRID: Number((benchmark.modes.HYBRID.evidence_accuracy * 100).toFixed(1)),
    },
  ] : [];

  const modesList: Array<{ key: 'RULE_BASED' | 'AI_ONLY' | 'HYBRID'; label: string; desc: string }> = [
    { 
      key: 'RULE_BASED', 
      label: 'RULE_BASED', 
      desc: 'Deterministic relational and financial rule engine without neural embeddings' 
    },
    { 
      key: 'AI_ONLY', 
      label: 'AI_ONLY', 
      desc: 'Prompt/LLM and semantic reasoning without deterministic decimal verification' 
    },
    { 
      key: 'HYBRID', 
      label: 'HYBRID', 
      desc: 'Integrated pipeline combining deterministic rules, vector embeddings, and LLM explanation' 
    }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Header & Run Evaluation Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-indigo-400" />
            <span>Reconciliation Evaluation & Benchmark Suite</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical evaluation of reconciliation architectures against ground-truth MSME transaction datasets
          </p>
        </div>

        {/* Run Evaluation Button */}
        <button
          onClick={handleRunEvaluation}
          disabled={isRunning}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-50 self-start sm:self-auto"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Running Evaluation...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Evaluation</span>
            </>
          )}
        </button>
      </div>

      {/* Execution Status Banner */}
      {statusMessage && (
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-3 text-xs text-slate-300">
          {isRunning ? (
            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span className="flex-1 font-medium">{statusMessage}</span>
          {benchmark?.evaluated_at && !isRunning && (
            <span className="text-[11px] font-mono text-slate-400">
              Evaluated at {new Date(benchmark.evaluated_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/30 flex items-center gap-3 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-500 text-xs flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          <span>Loading evaluation environment...</span>
        </div>
      ) : !benchmark ? (
        /* Empty State */
        <div className="p-16 text-center rounded-3xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="p-4 rounded-2xl bg-slate-800/50 w-fit mx-auto text-slate-400">
            <Clock className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-200">Evaluation not yet performed.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Click the "Run Evaluation" button above to benchmark RULE_BASED, AI_ONLY, and HYBRID reconciliation models across ground-truth test cases.
            </p>
          </div>
          <button
            onClick={handleRunEvaluation}
            disabled={isRunning}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Run Evaluation</span>
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          
          {/* Section 1: Measured Metrics Summary Cards for 3 Architectures */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {modesList.map((m) => {
              const metrics = benchmark.modes[m.key];
              return (
                <div 
                  key={m.key} 
                  className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm flex flex-col justify-between"
                >
                  <div className="space-y-1.5 border-b border-slate-800/80 pb-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-extrabold font-mono text-slate-100">{m.label}</h3>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                        {metrics.avg_latency_ms} ms avg
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {m.desc}
                    </p>
                  </div>

                  {/* 5 Core Metrics */}
                  <div className="space-y-2.5 text-xs">
                    
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Precision:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(metrics.precision * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Recall:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(metrics.recall * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">F1-Score:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(metrics.f1_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Reconciliation Accuracy:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(metrics.reconciliation_accuracy * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Evidence Accuracy:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(metrics.evidence_accuracy * 100).toFixed(1)}%
                      </span>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>

          {/* Section 2: Comparative Bar Chart */}
          <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  Measured Performance by Metric Across Modes
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Tested on {benchmark.total_test_cases} Ground-Truth Test Cases
              </span>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                  <XAxis dataKey="metric" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                  <Tooltip 
                    formatter={(val: any) => [`${val}%`, '']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} 
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="RULE_BASED" fill="#64748b" radius={[4, 4, 0, 0]} name="RULE_BASED" />
                  <Bar dataKey="AI_ONLY" fill="#a855f7" radius={[4, 4, 0, 0]} name="AI_ONLY" />
                  <Bar dataKey="HYBRID" fill="#6366f1" radius={[4, 4, 0, 0]} name="HYBRID" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Section 3: Comparative Results Table */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  Detailed Metric Measurement Table
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Micro-Averaged Benchmark Results
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                    <th className="p-3.5 font-semibold">Mode</th>
                    <th className="p-3.5 font-semibold text-center">Precision</th>
                    <th className="p-3.5 font-semibold text-center">Recall</th>
                    <th className="p-3.5 font-semibold text-center">F1</th>
                    <th className="p-3.5 font-semibold text-center">Reconciliation Accuracy</th>
                    <th className="p-3.5 font-semibold text-center">Evidence Accuracy</th>
                    <th className="p-3.5 font-semibold text-right">Avg Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 font-mono">
                  {modesList.map((m) => {
                    const data = benchmark.modes[m.key];
                    return (
                      <tr key={m.key} className="hover:bg-slate-800/30 transition-colors">
                        <td className="p-3.5 font-bold font-mono text-slate-200">
                          {m.label}
                        </td>
                        <td className="p-3.5 text-center text-slate-200">
                          {(data.precision * 100).toFixed(1)}%
                        </td>
                        <td className="p-3.5 text-center text-slate-200">
                          {(data.recall * 100).toFixed(1)}%
                        </td>
                        <td className="p-3.5 text-center text-slate-200">
                          {(data.f1_score * 100).toFixed(1)}%
                        </td>
                        <td className="p-3.5 text-center text-slate-200">
                          {(data.reconciliation_accuracy * 100).toFixed(1)}%
                        </td>
                        <td className="p-3.5 text-center text-slate-200">
                          {(data.evidence_accuracy * 100).toFixed(1)}%
                        </td>
                        <td className="p-3.5 text-right text-slate-400">
                          {data.avg_latency_ms} ms
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 4: Individual Test Cases Ground-Truth Evaluation Matrix */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 overflow-hidden space-y-0">
            <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  Ground-Truth Scenario Breakdown
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {benchmark.total_test_cases} Test Scenarios Evaluated
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                    <th className="p-3.5 font-semibold">Scenario ID & Title</th>
                    <th className="p-3.5 font-semibold">Expected Findings</th>
                    <th className="p-3.5 font-semibold text-center">RULE_BASED F1</th>
                    <th className="p-3.5 font-semibold text-center">AI_ONLY F1</th>
                    <th className="p-3.5 font-semibold text-center">HYBRID F1</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {benchmark.modes.HYBRID.cases.map((c, idx) => {
                    const ruleCase = benchmark.modes.RULE_BASED.cases[idx];
                    const aiCase = benchmark.modes.AI_ONLY.cases[idx];
                    return (
                      <tr key={c.case_id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="p-3.5">
                          <p className="font-mono font-bold text-slate-200">{c.case_id}</p>
                          <p className="text-[11px] text-slate-400">{c.title}</p>
                        </td>
                        <td className="p-3.5">
                          {c.expected.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {c.expected.map((e) => (
                                <span key={e} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                  {e}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-emerald-400 font-medium text-xs">Zero Discrepancies (Clean Match)</span>
                          )}
                        </td>
                        <td className="p-3.5 text-center font-mono text-slate-300">
                          {ruleCase ? `${(ruleCase.f1 * 100).toFixed(0)}%` : '—'}
                        </td>
                        <td className="p-3.5 text-center font-mono text-slate-300">
                          {aiCase ? `${(aiCase.f1 * 100).toFixed(0)}%` : '—'}
                        </td>
                        <td className="p-3.5 text-center font-mono text-slate-300">
                          {(c.f1 * 100).toFixed(0)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 5: Document Classifier Evaluation */}
          {classifierMetrics && (
            <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-sm font-bold text-slate-100">
                      Supervised Document Classifier (Model 1)
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    TF-IDF + Calibrated Logistic Regression trained on labelled MSME business documents
                  </p>
                </div>
                <div className="text-xs font-mono font-bold text-slate-200 bg-slate-800 px-3 py-1 rounded-lg border border-slate-700">
                  Overall Accuracy: {(classifierMetrics.accuracy * 100).toFixed(1)}%
                </div>
              </div>

              {/* Classification Report */}
              <div className="border border-slate-800 rounded-2xl overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                      <th className="p-3 font-semibold">Document Class</th>
                      <th className="p-3 font-semibold text-center">Precision</th>
                      <th className="p-3 font-semibold text-center">Recall</th>
                      <th className="p-3 font-semibold text-center">F1</th>
                      <th className="p-3 font-semibold text-right">Support</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 font-mono">
                    {classifierMetrics.labels.map((lbl) => {
                      const r = classifierMetrics.classification_report[lbl] || {};
                      return (
                        <tr key={lbl} className="hover:bg-slate-800/30">
                          <td className="p-3 font-sans font-medium text-slate-300">{lbl}</td>
                          <td className="p-3 text-center text-slate-200">{(r.precision * 100).toFixed(1)}%</td>
                          <td className="p-3 text-center text-slate-200">{(r.recall * 100).toFixed(1)}%</td>
                          <td className="p-3 text-center text-slate-200">{(r['f1-score'] * 100).toFixed(1)}%</td>
                          <td className="p-3 text-right text-slate-400">{r.support}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Confusion Matrix */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Confusion Matrix
                </h4>
                <div className="overflow-x-auto border border-slate-800 rounded-2xl p-4 bg-slate-950/80">
                  <table className="text-xs text-center border-collapse mx-auto">
                    <thead>
                      <tr>
                        <th className="p-2 text-slate-500 font-normal">True \ Pred</th>
                        {classifierMetrics.labels.map((l) => (
                          <th key={l} className="p-2 text-[10px] font-mono text-slate-400 max-w-[80px] truncate">
                            {l.replace('_', ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {classifierMetrics.confusion_matrix.map((row, rIdx) => (
                        <tr key={rIdx}>
                          <td className="p-2 text-[10px] font-mono text-slate-400 font-bold text-left max-w-[90px] truncate">
                            {classifierMetrics.labels[rIdx].replace('_', ' ')}
                          </td>
                          {row.map((val, cIdx) => (
                            <td 
                              key={cIdx} 
                              className={`p-2 font-mono text-xs ${
                                rIdx === cIdx 
                                  ? 'bg-indigo-600/30 text-indigo-300 font-bold rounded' 
                                  : (val > 0 ? 'bg-rose-600/20 text-rose-300' : 'text-slate-600')
                              }`}
                            >
                              {val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
};
