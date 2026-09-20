import React, { useState } from 'react';
import { ArrowLeftRight } from 'lucide-react';
import type { DocumentItem } from '../../types';
import { DocTypeBadge } from '../common/Badge';

interface EvidenceInspectorProps {
  documents: DocumentItem[];
}

export const EvidenceInspector: React.FC<EvidenceInspectorProps> = ({ documents }) => {
  const [selectedDocIdA, setSelectedDocIdA] = useState<string>(documents[0]?.id || '');
  const [selectedDocIdB, setSelectedDocIdB] = useState<string>(documents[1]?.id || documents[0]?.id || '');

  const docA = documents.find(d => d.id === selectedDocIdA);
  const docB = documents.find(d => d.id === selectedDocIdB);

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4 text-indigo-400" />
            <h4 className="text-sm font-bold text-slate-100">Side-by-Side Evidence Inspector</h4>
          </div>
          <p className="text-xs text-slate-400">Direct multi-document line item & textual comparison</p>
        </div>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Document A Selector & Viewer */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400">Doc A:</span>
            <select
              value={selectedDocIdA}
              onChange={(e) => setSelectedDocIdA(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  [{d.doc_type}] {d.filename}
                </option>
              ))}
            </select>
          </div>

          {docA && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 min-h-[260px]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-200 truncate">{docA.filename}</span>
                <DocTypeBadge type={docA.doc_type} confidence={docA.classification_confidence} />
              </div>

              {/* Parsed Line Items Table */}
              {docA.parsed_data?.items && docA.parsed_data.items.length > 0 ? (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Line Items</p>
                  <div className="max-h-40 overflow-y-auto space-y-1 pr-1">
                    {docA.parsed_data.items.map((it, idx) => (
                      <div key={idx} className="p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px] flex justify-between items-center">
                        <span className="font-medium text-slate-300 truncate max-w-[140px]">{it.description}</span>
                        <span className="text-slate-400 font-mono">{it.quantity} {it.unit}</span>
                        <span className="font-bold text-emerald-400 font-mono">₹{it.unit_price}/unit</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Extracted Text Preview</p>
                  <pre className="p-2.5 rounded bg-slate-900 border border-slate-800/80 font-mono text-[10px] text-slate-300 max-h-40 overflow-y-auto whitespace-pre-wrap">
                    {docA.raw_text.slice(0, 600)}...
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Document B Selector & Viewer */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400">Doc B:</span>
            <select
              value={selectedDocIdB}
              onChange={(e) => setSelectedDocIdB(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  [{d.doc_type}] {d.filename}
                </option>
              ))}
            </select>
          </div>

          {docB && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 min-h-[260px]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-200 truncate">{docB.filename}</span>
                <DocTypeBadge type={docB.doc_type} confidence={docB.classification_confidence} />
              </div>

              {/* Parsed Line Items Table */}
              {docB.parsed_data?.items && docB.parsed_data.items.length > 0 ? (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Line Items</p>
                  <div className="max-h-40 overflow-y-auto space-y-1 pr-1">
                    {docB.parsed_data.items.map((it, idx) => (
                      <div key={idx} className="p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px] flex justify-between items-center">
                        <span className="font-medium text-slate-300 truncate max-w-[140px]">{it.description}</span>
                        <span className="text-slate-400 font-mono">{it.quantity} {it.unit}</span>
                        <span className="font-bold text-emerald-400 font-mono">₹{it.unit_price}/unit</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Extracted Text Preview</p>
                  <pre className="p-2.5 rounded bg-slate-900 border border-slate-800/80 font-mono text-[10px] text-slate-300 max-h-40 overflow-y-auto whitespace-pre-wrap">
                    {docB.raw_text.slice(0, 600)}...
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
