"""
TRACE - Transaction Linker Service
Groups ingested documents into coherent business transaction graphs using identifier references and semantic heuristics.
"""

from typing import List, Dict, Any, Tuple
from app.semantic.matcher import semantic_matcher

class TransactionLinker:
    @staticmethod
    def identify_transaction_ref(documents: List[Dict[str, Any]]) -> str:
        """
        Determines the canonical transaction reference for a cluster of documents.
        Prioritizes PO Number, then Invoice Number, then first document number.
        """
        po_num = None
        inv_ref = None
        inv_num = None

        for doc in documents:
            p_data = doc.get("parsed_data", {})
            d_type = doc.get("doc_type")
            doc_num = p_data.get("document_number")
            po_ref = p_data.get("po_reference")
            inv_r = p_data.get("invoice_reference")

            if d_type == "PURCHASE_ORDER" and doc_num:
                po_num = doc_num
            if po_ref and not po_num:
                po_num = po_ref
            if d_type == "INVOICE" and doc_num:
                inv_num = doc_num
            if inv_r and not inv_ref:
                inv_ref = inv_r

        return po_num or inv_ref or inv_num or f"TXN-{documents[0].get('id', 'BATCH')[:8].upper()}"

    @staticmethod
    def group_documents_into_transactions(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups a batch of uploaded documents into separate transactions using
        graph connected components over PO numbers, Invoice references, Delivery Challans,
        and transaction batch identifiers.
        """
        import re
        from collections import defaultdict

        if not documents:
            return {}

        # 1. Extract all identifier keys for each document
        doc_keys: List[List[str]] = []
        for doc in documents:
            p_data = doc.get("parsed_data", {})
            d_type = doc.get("doc_type", "UNKNOWN")
            fn = doc.get("filename", "")
            
            keys = set()
            
            # Filename-based transaction tokens (e.g. TXN-001, TXN-2024-001)
            txn_fn_match = re.search(r"(TXN[_-]\w+)", fn, re.IGNORECASE)
            if txn_fn_match:
                keys.add(f"TXN:{txn_fn_match.group(1).upper().replace('_', '-')}")

            # PO References
            po_num = p_data.get("document_number") if d_type == "PURCHASE_ORDER" else None
            po_ref = p_data.get("po_reference")
            if po_num:
                keys.add(f"PO:{po_num.strip().upper()}")
            if po_ref:
                keys.add(f"PO:{po_ref.strip().upper()}")

            # Invoice References
            inv_num = p_data.get("document_number") if d_type == "INVOICE" else None
            inv_ref = p_data.get("invoice_reference")
            if inv_num:
                keys.add(f"INV:{inv_num.strip().upper()}")
            if inv_ref:
                keys.add(f"INV:{inv_ref.strip().upper()}")

            # Other document numbers
            doc_num = p_data.get("document_number")
            if doc_num and not po_num and not inv_num:
                keys.add(f"DOC:{doc_num.strip().upper()}")

            # Fallback if no structured keys
            if not keys:
                keys.add(f"DOC_ID:{doc.get('id', 'UNKNOWN')}")

            doc_keys.append(list(keys))

        # 2. Build Adjacency Graph of Document Indices
        # Connect doc i and doc j if they share any identifier key
        key_to_doc_indices = defaultdict(list)
        for doc_idx, keys in enumerate(doc_keys):
            for k in keys:
                key_to_doc_indices[k].append(doc_idx)

        adj = defaultdict(set)
        for k, indices in key_to_doc_indices.items():
            for i in indices:
                for j in indices:
                    if i != j:
                        adj[i].add(j)

        # 3. Find Connected Components via BFS/DFS
        visited = set()
        components: List[List[int]] = []
        for i in range(len(documents)):
            if i not in visited:
                comp = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        # 4. Form Clusters with Canonical Reference
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for comp_indices in components:
            comp_docs = [documents[idx] for idx in comp_indices]
            
            # Determine best canonical reference for the cluster
            canonical_ref = None
            all_comp_keys = [k for idx in comp_indices for k in doc_keys[idx]]
            
            # Priority 1: PO Number
            for k in all_comp_keys:
                if k.startswith("PO:"):
                    canonical_ref = k.split("PO:", 1)[1]
                    break
            # Priority 2: TXN token
            if not canonical_ref:
                for k in all_comp_keys:
                    if k.startswith("TXN:"):
                        canonical_ref = k.split("TXN:", 1)[1]
                        break
            # Priority 3: Invoice Number
            if not canonical_ref:
                for k in all_comp_keys:
                    if k.startswith("INV:"):
                        canonical_ref = k.split("INV:", 1)[1]
                        break
            # Priority 4: First Document Number
            if not canonical_ref:
                for k in all_comp_keys:
                    if k.startswith("DOC:"):
                        canonical_ref = k.split("DOC:", 1)[1]
                        break
            if not canonical_ref:
                canonical_ref = f"TXN-{comp_docs[0].get('id', 'BATCH')[:8].upper()}"

            clusters[canonical_ref] = comp_docs

        return clusters

    @staticmethod
    def link_database_documents(db) -> List[Any]:
        """
        Scans all documents in DB, links them into Transaction clusters, and persists them.
        """
        import uuid
        from app.models.document import Document
        from app.models.transaction import Transaction

        docs = db.query(Document).all()
        if not docs:
            return []

        doc_dicts = [
            {
                "id": d.id,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "parsed_data": d.parsed_data or {},
                "raw_text": d.raw_text,
                "orm_doc": d
            }
            for d in docs
        ]

        clusters = TransactionLinker.group_documents_into_transactions(doc_dicts)

        for ref_key, cluster_docs in clusters.items():
            existing_txn = db.query(Transaction).filter(Transaction.transaction_ref == ref_key).first()
            supplier = ""
            customer = ""
            total_amt = 0.0
            for cd in cluster_docs:
                p = cd.get("parsed_data", {})
                if not supplier and p.get("supplier_name"):
                    supplier = p.get("supplier_name")
                if not customer and p.get("customer_name"):
                    customer = p.get("customer_name")
                gt = float(p.get("grand_total") or p.get("payment_amount") or 0.0)
                if gt > total_amt:
                    total_amt = gt

            if not existing_txn:
                txn_id = f"txn_{uuid.uuid4().hex[:10]}"
                txn = Transaction(
                    id=txn_id,
                    transaction_ref=ref_key,
                    title=f"Transaction {ref_key} ({supplier or 'MSME'})",
                    supplier_name=supplier,
                    customer_name=customer,
                    total_amount=total_amt,
                    reconciliation_status="PENDING"
                )
                for cd in cluster_docs:
                    txn.documents.append(cd["orm_doc"])
                db.add(txn)
            else:
                for cd in cluster_docs:
                    if cd["orm_doc"] not in existing_txn.documents:
                        existing_txn.documents.append(cd["orm_doc"])
                if total_amt > existing_txn.total_amount:
                    existing_txn.total_amount = total_amt
                if supplier and not existing_txn.supplier_name:
                    existing_txn.supplier_name = supplier

        db.commit()
        return db.query(Transaction).all()

transaction_linker = TransactionLinker()
