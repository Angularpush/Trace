import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Upload, 
  Trash2, 
  Search, 
  Cpu, 
  Loader2
} from 'lucide-react';
import { api } from '../api';
import type { DocumentItem } from '../types';
import { DocTypeBadge } from '../components/common/Badge';
import { DocumentUploadModal } from '../components/upload/DocumentUploadModal';

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDocs = async () => {
    setIsLoading(true);
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      await api.deleteDocument(id);
      if (selectedDoc?.id === id) setSelectedDoc(null);
      fetchDocs();
    }
  };

  const docTypes: Array<{ label: string; value: string }> = [
    { label: 'All Documents', value: 'ALL' },
    { label: 'Purchase Orders', value: 'PURCHASE_ORDER' },
    { label: 'Tax Invoices', value: 'INVOICE' },
    { label: 'Delivery Notes', value: 'DELIVERY_NOTE' },
    { label: 'Payment Receipts', value: 'PAYMENT_RECEIPT' },
    { label: 'Quotations', value: 'QUOTATION' },
    { label: 'Credit Notes', value: 'CREDIT_NOTE' },
    { label: 'Debit Notes', value: 'DEBIT_NOTE' },
  ];

  const filteredDocs = documents.filter((doc) => {
    const matchesType = selectedType === 'ALL' || doc.doc_type === selectedType;
    const matchesSearch = 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.parsed_data?.document_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.parsed_data?.supplier_name?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100">Document Processing Hub</h1>
          <p className="text-xs text-slate-400">
            Automated PDF extraction, TF-IDF + Logistic Regression classification, and normalization
          </p>
        </div>
        <button
          onClick={() => setIsUploadOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition cursor-pointer self-start sm:self-auto"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Documents</span>
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
        
        {/* Document Type Badges */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {docTypes.map((dt) => (
            <button
              key={dt.value}
              onClick={() => setSelectedType(dt.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedType === dt.value
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {dt.label}
            </button>
          ))}
        </div>

        {/* Search Box */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, ref, vendor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950/80 border border-slate-700/60 rounded-xl text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

      </div>

      {/* Document Grid / Table View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* List of Documents (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          {isLoading ? (
            <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/40 space-y-3">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Loading documents...</p>
            </div>
          ) : filteredDocs.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {filteredDocs.map((doc) => {
                const isSelected = selectedDoc?.id === doc.id;
                return (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-3 ${
                      isSelected
                        ? 'bg-indigo-950/20 border-indigo-500/50 shadow-md shadow-indigo-500/5'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                        <span className="font-bold text-xs text-slate-100 truncate">{doc.filename}</span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(doc.id);
                        }}
                        className="text-slate-500 hover:text-rose-400 p-1 rounded transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <DocTypeBadge type={doc.doc_type || doc.document_type || 'UNKNOWN'} confidence={doc.classification_confidence ?? doc.confidence} />
                      <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
                        {doc.page_number && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono font-semibold">
                            Page {doc.page_number}
                          </span>
                        )}
                        <span>{doc.page_count || 1} page(s)</span>
                      </div>
                    </div>

                    {/* Metadata chips */}
                    <div className="text-[11px] text-slate-400 space-y-1 font-mono">
                      {doc.parsed_data?.document_number && (
                        <p className="truncate"><b>No:</b> {doc.parsed_data.document_number}</p>
                      )}
                      {doc.parsed_data?.supplier_name && (
                        <p className="truncate font-sans text-slate-300"><b>Vendor:</b> {doc.parsed_data.supplier_name}</p>
                      )}
                      {doc.parsed_data?.grand_total && parseFloat(String(doc.parsed_data.grand_total)) > 0 && (
                        <p className="text-emerald-400 font-bold">
                          Total: ₹{parseFloat(String(doc.parsed_data.grand_total)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </p>
                      )}
                    </div>

                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/40 text-slate-500 text-xs">
              No documents matched the criteria.
            </div>
          )}
        </div>

        {/* Selected Document Details Inspector (1 Col) */}
        <div className="lg:col-span-1">
          {selectedDoc ? (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5 sticky top-24">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="truncate">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-slate-100 truncate">{selectedDoc.filename}</h3>
                    {selectedDoc.page_number && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50 text-[10px] font-mono font-bold">
                        Page {selectedDoc.page_number}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-400">ID: {selectedDoc.id}</p>
                </div>
                <DocTypeBadge type={selectedDoc.doc_type || selectedDoc.document_type || 'UNKNOWN'} confidence={selectedDoc.classification_confidence ?? selectedDoc.confidence} />
              </div>

              {/* Classifier Probability Distribution */}
              {selectedDoc.parsed_data?.prob_dist && (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                    <span>ML Classifier Probabilities</span>
                  </div>
                  <div className="space-y-1 bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 max-h-32 overflow-y-auto">
                    {Object.entries(selectedDoc.parsed_data.prob_dist).map(([label, prob]) => (
                      <div key={label} className="flex items-center justify-between text-[10px]">
                        <span className="text-slate-400">{label}</span>
                        <span className="font-mono font-bold text-slate-200">{(prob * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted Line Items */}
              {selectedDoc.parsed_data?.items && selectedDoc.parsed_data.items.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-300">Parsed Line Items ({selectedDoc.parsed_data.items.length})</p>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {selectedDoc.parsed_data.items.map((it, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                        <div className="flex justify-between font-bold text-slate-200">
                          <span className="truncate max-w-[150px]">{it.description}</span>
                          <span className="text-emerald-400 font-mono">₹{it.unit_price}/unit</span>
                        </div>
                        <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                          <span>Qty: {it.quantity} {it.unit}</span>
                          <span>Line Total: ₹{it.total_amount}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw OCR Text Snippet */}
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-slate-300">Extracted Raw Text</p>
                <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-mono max-h-44 overflow-y-auto whitespace-pre-wrap">
                  {selectedDoc.raw_text || selectedDoc.extracted_text}
                </pre>
              </div>

            </div>
          ) : (
            <div className="p-8 text-center border border-slate-800 rounded-2xl bg-slate-900/40 text-slate-500 text-xs">
              Select any document on the left to view parsed line items, classification confidence, and raw text.
            </div>
          )}
        </div>

      </div>

      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => fetchDocs()}
        onNavigateToTransaction={(txnId) => {
          navigate(`/transactions/${txnId}`);
        }}
      />

    </div>
  );
};
