import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  RefreshCw, 
  Search, 
  Upload, 
  Loader2, 
  CheckCircle2, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Filter, 
  Layers,
  AlertCircle,
  Clock,
  ArrowUpRight,
  Database
  Database,
  Trash2
} from 'lucide-react';
import { api } from '../api';
import type { TransactionItem, SeverityLevel } from '../types';
import { StatusBadge, SeverityBadge } from '../components/common/Badge';
import { DocumentUploadModal } from '../components/upload/DocumentUploadModal';

type SortField = 'transaction_ref' | 'supplier_name' | 'customer_name' | 'documents_count' | 'invoice_amount' | 'paid_amount' | 'outstanding' | 'status' | 'discrepancies_count' | 'updated_at';
type SortOrder = 'asc' | 'desc';

export const TransactionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLinking, setIsLinking] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  // Sorting
  const [sortField, setSortField] = useState<SortField>('updated_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const data = await api.listTransactions();
      setTransactions(data);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCleanupEmpty = async () => {
    if (!window.confirm("Remove all 0.00 / empty transaction records?")) return;
    setIsCleaning(true);
    try {
      await api.cleanupEmptyTransactions();
      await fetchTransactions();
    } catch (err) {
      console.error('Cleanup failed:', err);
    } finally {
      setIsCleaning(false);
    }
  };

  const handleDeleteTransaction = async (e: React.MouseEvent, txnId: string) => {
    e.stopPropagation();
    if (!window.confirm("Delete this transaction?")) return;
    try {
      await api.deleteTransaction(txnId);
      await fetchTransactions();
    } catch (err) {
      console.error('Delete transaction failed:', err);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleAutoLink = async () => {
    setIsLinking(true);
    try {
      const data = await api.autoLinkTransactions();
      setTransactions(data);
    } catch (err) {
      console.error('Auto link failed:', err);
    } finally {
      setIsLinking(false);
    }
  };

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      await api.seedDemo();
      await fetchTransactions();
    } catch (err) {
      console.error('Seed demo failed:', err);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  // Helper calculation per transaction
  const getTransactionMetrics = (t: TransactionItem) => {
    const docs = t.documents || [];
    const discs = t.discrepancies || [];
    
    // Invoiced Amount
    const invoiceDoc = docs.find(d => d.doc_type === 'INVOICE');
    const invoiceAmount = Number(invoiceDoc?.parsed_data?.grand_total || t.total_amount) || 0;

    // Paid Amount from Payment Receipt
    const paymentDoc = docs.find(d => d.doc_type === 'PAYMENT_RECEIPT');
    const paymentShortfall = discs
      .filter(d => d.rule_code === 'R003' || d.discrepancy_type === 'PAYMENT_SHORTFALL')
      .reduce((acc, d) => acc + (d.difference_amount || 0), 0);

    let paidAmount = 0;
    if (paymentDoc) {
      paidAmount = Number(paymentDoc.parsed_data?.grand_total || paymentDoc.parsed_data?.payment_amount || 0);
      if (paidAmount === 0 && invoiceAmount > 0) {
        paidAmount = Math.max(0, invoiceAmount - paymentShortfall);
      }
    } else if (t.reconciliation_status === 'RECONCILED' && invoiceAmount > 0) {
      paidAmount = invoiceAmount;
    }

    // Outstanding Shortfall
    const outstanding = paymentShortfall > 0 
      ? paymentShortfall 
      : Math.max(0, invoiceAmount - paidAmount);

    // Highest Severity
    let highestSeverity: SeverityLevel | 'CLEAN' = 'CLEAN';
    if (discs.some(d => d.severity === 'CRITICAL')) highestSeverity = 'CRITICAL';
    else if (discs.some(d => d.severity === 'HIGH')) highestSeverity = 'HIGH';
    else if (discs.some(d => d.severity === 'MEDIUM')) highestSeverity = 'MEDIUM';
    else if (discs.some(d => d.severity === 'LOW')) highestSeverity = 'LOW';

    return {
      invoiceAmount,
      paidAmount,
      outstanding,
      discrepancyCount: discs.length,
      highestSeverity,
      documentsCount: docs.length
    };
  };

  // Filtered and Sorted Transactions
  const processedTransactions = useMemo(() => {
    let result = transactions.filter((t) => {
      const metrics = getTransactionMetrics(t);
      
      // Search
      const search = searchQuery.toLowerCase().trim();
      const matchesSearch = !search || 
        t.transaction_ref.toLowerCase().includes(search) ||
        (t.supplier_name && t.supplier_name.toLowerCase().includes(search)) ||
        (t.customer_name && t.customer_name.toLowerCase().includes(search)) ||
        (t.title && t.title.toLowerCase().includes(search));

      // Status filter
      const matchesStatus = statusFilter === 'ALL' || t.reconciliation_status === statusFilter;

      // Severity filter
      let matchesSeverity = true;
      if (severityFilter !== 'ALL') {
        if (severityFilter === 'CLEAN') {
          matchesSeverity = metrics.discrepancyCount === 0;
        } else {
          matchesSeverity = t.discrepancies?.some(d => d.severity === severityFilter) || false;
        }
      }

      return matchesSearch && matchesStatus && matchesSeverity;
    });

    // Sorting
    result.sort((a, b) => {
      const metA = getTransactionMetrics(a);
      const metB = getTransactionMetrics(b);

      let comparison = 0;
      switch (sortField) {
        case 'transaction_ref':
          comparison = a.transaction_ref.localeCompare(b.transaction_ref);
          break;
        case 'supplier_name':
          comparison = (a.supplier_name || '').localeCompare(b.supplier_name || '');
          break;
        case 'customer_name':
          comparison = (a.customer_name || '').localeCompare(b.customer_name || '');
          break;
        case 'documents_count':
          comparison = metA.documentsCount - metB.documentsCount;
          break;
        case 'invoice_amount':
          comparison = metA.invoiceAmount - metB.invoiceAmount;
          break;
        case 'paid_amount':
          comparison = metA.paidAmount - metB.paidAmount;
          break;
        case 'outstanding':
          comparison = metA.outstanding - metB.outstanding;
          break;
        case 'status':
          comparison = a.reconciliation_status.localeCompare(b.reconciliation_status);
          break;
        case 'discrepancies_count':
          comparison = metA.discrepancyCount - metB.discrepancyCount;
          break;
        case 'updated_at':
        default:
          comparison = new Date(a.updated_at || a.created_at).getTime() - new Date(b.updated_at || b.created_at).getTime();
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [transactions, searchQuery, statusFilter, severityFilter, sortField, sortOrder]);

  // Pagination Slice
  const totalPages = Math.max(1, Math.ceil(processedTransactions.length / pageSize));
  const paginatedTransactions = processedTransactions.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const formatDate = (isoString?: string) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-slate-600 group-hover:text-slate-400 inline ml-1 transition" />;
    }
    return sortOrder === 'asc' ? (
      <ArrowUp className="w-3 h-3 text-indigo-400 inline ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 text-indigo-400 inline ml-1" />
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-indigo-400" />
            <span>MSME Multi-Document Transactions</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated graph-clustered transactions linked by POs, Tax Invoices, Delivery Notes, and Payment Records
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Batch</span>
          </button>
          
          <button
            onClick={handleSeedDemo}
            disabled={isSeeding}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/30 text-emerald-300 text-xs font-bold transition cursor-pointer disabled:opacity-50"
          >
            {isSeeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
            <span>Load Demo</span>
          </button>

          <button
            onClick={handleAutoLink}
            disabled={isLinking}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLinking ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Auto-Link TXNs</span>
          </button>

          <button
            onClick={handleCleanupEmpty}
            disabled={isCleaning}
            title="Remove all zero-amount or empty documents/transactions"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 text-xs font-semibold border border-rose-500/30 transition cursor-pointer disabled:opacity-50"
          >
            {isCleaning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
            <span>Clear 0-Records</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3.5 p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
        
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by ID, Supplier, Customer..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-3.5 py-2 text-xs bg-slate-950/80 border border-slate-700/60 rounded-xl text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="text-slate-400 text-[11px] font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900 text-slate-200">All Statuses</option>
              <option value="RECONCILED" className="bg-slate-900 text-slate-200">Reconciled</option>
              <option value="DISCREPANCY_FOUND" className="bg-slate-900 text-slate-200">Discrepancy Detected</option>
              <option value="MINOR_VARIANCE" className="bg-slate-900 text-slate-200">Minor Variance</option>
              <option value="INCOMPLETE" className="bg-slate-900 text-slate-200">Incomplete Docs</option>
              <option value="PENDING" className="bg-slate-900 text-slate-200">Pending Audit</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="text-slate-400 text-[11px] font-semibold">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900 text-slate-200">All Severities</option>
              <option value="CRITICAL" className="bg-slate-900 text-slate-200">Critical</option>
              <option value="HIGH" className="bg-slate-900 text-slate-200">High</option>
              <option value="MEDIUM" className="bg-slate-900 text-slate-200">Medium</option>
              <option value="LOW" className="bg-slate-900 text-slate-200">Low</option>
              <option value="CLEAN" className="bg-slate-900 text-slate-200">0 Issues (Clean)</option>
            </select>
          </div>

          {/* Reset Filters */}
          {(searchQuery || statusFilter !== 'ALL' || severityFilter !== 'ALL') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('ALL');
                setSeverityFilter('ALL');
                setCurrentPage(1);
              }}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold px-2 py-1 transition"
            >
              Reset Filters
            </button>
          )}

        </div>

      </div>

      {/* Transactions Table */}
      <div className="border border-slate-800 rounded-3xl bg-slate-900/60 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/90 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider font-bold">
                
                {/* 1. Transaction ID */}
                <th 
                  onClick={() => handleSort('transaction_ref')}
                  className="py-3.5 px-4 cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Transaction ID</span>
                  {renderSortIcon('transaction_ref')}
                </th>

                {/* 2. Supplier */}
                <th 
                  onClick={() => handleSort('supplier_name')}
                  className="py-3.5 px-4 cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Supplier</span>
                  {renderSortIcon('supplier_name')}
                </th>

                {/* 3. Customer */}
                <th 
                  onClick={() => handleSort('customer_name')}
                  className="py-3.5 px-4 cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Customer</span>
                  {renderSortIcon('customer_name')}
                </th>

                {/* 4. Documents */}
                <th 
                  onClick={() => handleSort('documents_count')}
                  className="py-3.5 px-3 text-center cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Documents</span>
                  {renderSortIcon('documents_count')}
                </th>

                {/* 5. Invoice Amount */}
                <th 
                  onClick={() => handleSort('invoice_amount')}
                  className="py-3.5 px-3 text-right cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Invoice Amount</span>
                  {renderSortIcon('invoice_amount')}
                </th>

                {/* 6. Paid Amount */}
                <th 
                  onClick={() => handleSort('paid_amount')}
                  className="py-3.5 px-3 text-right cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Paid Amount</span>
                  {renderSortIcon('paid_amount')}
                </th>

                {/* 7. Outstanding */}
                <th 
                  onClick={() => handleSort('outstanding')}
                  className="py-3.5 px-3 text-right cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Outstanding</span>
                  {renderSortIcon('outstanding')}
                </th>

                {/* 8. Status */}
                <th 
                  onClick={() => handleSort('status')}
                  className="py-3.5 px-3 text-center cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Status</span>
                  {renderSortIcon('status')}
                </th>

                {/* 9. Discrepancies */}
                <th 
                  onClick={() => handleSort('discrepancies_count')}
                  className="py-3.5 px-3 text-center cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Discrepancies</span>
                  {renderSortIcon('discrepancies_count')}
                </th>

                {/* 10. Last Reconciled */}
                <th 
                  onClick={() => handleSort('updated_at')}
                  className="py-3.5 px-4 cursor-pointer hover:text-slate-200 transition group select-none"
                >
                  <span>Last Reconciled</span>
                  {renderSortIcon('updated_at')}
                </th>

                <th className="py-3.5 px-3 text-right"></th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800/60 font-medium">
              {isLoading ? (
                <tr>
                  <td colSpan={11} className="py-16 text-center text-slate-400">
                    <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-2" />
                    <p className="text-xs">Loading transaction records...</p>
                  </td>
                </tr>
              ) : paginatedTransactions.length > 0 ? (
                paginatedTransactions.map((txn) => {
                  const met = getTransactionMetrics(txn);
                  const isShortfall = met.outstanding > 0;

                  return (
                    <tr
                      key={txn.id}
                      onClick={() => navigate(`/transactions/${txn.id}`)}
                      className="hover:bg-slate-800/40 transition cursor-pointer group"
                    >
                      
                      {/* 1. Transaction ID */}
                      <td className="py-3.5 px-4 font-mono font-bold text-indigo-300 group-hover:text-indigo-200">
                        <div className="flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                          <span className="truncate max-w-[130px]">{txn.transaction_ref}</span>
                        </div>
                      </td>

                      {/* 2. Supplier */}
                      <td className="py-3.5 px-4 text-slate-200">
                        <span className="truncate max-w-[140px] block font-semibold">
                          {txn.supplier_name || 'Generic Vendor'}
                        </span>
                      </td>

                      {/* 3. Customer */}
                      <td className="py-3.5 px-4 text-slate-400">
                        <span className="truncate max-w-[140px] block text-[11px]">
                          {txn.customer_name || 'MSME Buyer'}
                        </span>
                      </td>

                      {/* 4. Documents */}
                      <td className="py-3.5 px-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <span className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 font-mono text-[11px] text-slate-200 font-bold">
                            {met.documentsCount}
                          </span>
                        </div>
                      </td>

                      {/* 5. Invoice Amount */}
                      <td className="py-3.5 px-3 text-right font-mono text-slate-200 font-bold">
                        ₹{met.invoiceAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      {/* 6. Paid Amount */}
                      <td className="py-3.5 px-3 text-right font-mono text-emerald-400 font-bold">
                        ₹{met.paidAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      {/* 7. Outstanding */}
                      <td className="py-3.5 px-3 text-right font-mono">
                        {isShortfall ? (
                          <span className="text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20">
                            ₹{met.outstanding.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">₹0.00</span>
                        )}
                      </td>

                      {/* 8. Status */}
                      <td className="py-3.5 px-3 text-center">
                        <StatusBadge status={txn.reconciliation_status} />
                      </td>

                      {/* 9. Discrepancies */}
                      <td className="py-3.5 px-3 text-center">
                        {met.discrepancyCount > 0 ? (
                          <div className="flex items-center justify-center gap-1.5">
                            <SeverityBadge severity={met.highestSeverity} />
                            <span className="font-mono text-[11px] text-slate-300 font-bold">
                              ({met.discrepancyCount})
                            </span>
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Clean</span>
                          </span>
                        )}
                      </td>

                      {/* 10. Last Reconciled */}
                      <td className="py-3.5 px-4 text-slate-400 text-[11px] font-mono">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500 shrink-0" />
                          <span>{formatDate(txn.updated_at || txn.created_at)}</span>
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-3 text-right">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-600/10 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition">
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </span>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={(e) => handleDeleteTransaction(e, txn.id)}
                            title="Delete transaction"
                            className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500 hover:text-white transition cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                          <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-600/10 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition">
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </span>
                        </div>
                      </td>

                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={11} className="py-16 text-center text-slate-500 text-xs">
                    <div className="max-w-xs mx-auto space-y-2">
                      <Layers className="w-8 h-8 text-slate-600 mx-auto" />
                      <p className="font-semibold text-slate-300">No transactions matched your filters.</p>
                      <p className="text-[11px]">Try clearing your search query or status filter.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {processedTransactions.length > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-slate-800 bg-slate-950/80 text-xs text-slate-400">
            
            {/* Range info */}
            <div>
              Showing <b className="text-slate-200">{(currentPage - 1) * pageSize + 1}</b> to <b className="text-slate-200">{Math.min(currentPage * pageSize, processedTransactions.length)}</b> of <b className="text-slate-200">{processedTransactions.length}</b> transactions
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px]">Rows per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-slate-200 text-xs focus:outline-none"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>

              {/* Page Buttons */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                
                <span className="px-3 py-1 font-mono text-xs font-bold text-slate-200">
                  {currentPage} / {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 transition"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

          </div>
        )}

      </div>

      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => fetchTransactions()}
      />

    </div>
  );
};
