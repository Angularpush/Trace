import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/common/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { ReconciliationDetailPage } from './pages/ReconciliationDetailPage';
import { EvaluationPage } from './pages/EvaluationPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/transactions/:id" element={<ReconciliationDetailPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
          TRACE Decision-Support System • Multi-Document MSME Transaction Reconciliation
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
