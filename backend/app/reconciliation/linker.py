"""
TRACE - Multi-Signal Transaction Linker Service
Links heterogeneous documents into coherent transaction clusters using:
1. Exact document identifiers (PO #, Invoice #, Payment Ref)
2. Metadata matching (Supplier/Customer, Amounts, Dates)
3. Semantic similarity (Embeddings / TF-IDF on descriptions and entities)
4. Hybrid multi-signal fusion

Stores link provenance (method & confidence) in TransactionDocument.
"""

import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime

from app.semantic.matcher import semantic_matcher
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_entity_name

class TransactionLinker:
    """
    Multi-Signal Graph Linker for Document-Level MSME Transactions.
    """

    @staticmethod
    def extract_document_identifiers(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts structured linkage keys from a document record.
        """
        p_data = doc.get("parsed_data", {}) or {}
        d_type = doc.get("document_type") or doc.get("doc_type", "OTHER")
        fn = doc.get("filename", "")

        doc_num = p_data.get("document_number")
        po_ref = p_data.get("po_reference")
        inv_ref = p_data.get("invoice_reference")
        pay_ref = p_data.get("transaction_reference") or p_data.get("payment_reference")
        supplier = clean_entity_name(p_data.get("supplier_name") or "")
        customer = clean_entity_name(p_data.get("customer_name") or "")
        doc_date = normalize_date(p_data.get("document_date"))
        amount = normalize_decimal(p_data.get("grand_total") or p_data.get("payment_amount") or 0)
        items = p_data.get("items", []) or []

        # Extract filename tokens like TXN-001 or TXN_2024
        txn_token = None
        match = re.search(r"(TXN[_-][A-Za-z0-9]+)", fn, re.IGNORECASE)
        if match:
            txn_token = match.group(1).upper().replace("_", "-")

        return {
            "doc_id": doc.get("id"),
            "doc_type": d_type,
            "filename": fn,
            "doc_num": str(doc_num).strip().upper() if doc_num else None,
            "po_ref": str(po_ref).strip().upper() if po_ref else None,
            "inv_ref": str(inv_ref).strip().upper() if inv_ref else None,
            "pay_ref": str(pay_ref).strip().upper() if pay_ref else None,
            "txn_token": txn_token,
            "supplier": supplier,
            "customer": customer,
            "doc_date": doc_date,
            "amount": amount,
            "items": items,
            "file_id": doc.get("file_id"),
            "page_start": doc.get("page_start", 1),
            "page_end": doc.get("page_end", 1),
        }

    @staticmethod
    def evaluate_pair_link(meta_a: Dict[str, Any], meta_b: Dict[str, Any]) -> Tuple[bool, str, float, Dict[str, Any]]:
        """
        Evaluates whether two documents belong to the same transaction.
        Returns: (is_linked, link_method, confidence, link_details)
        """
        # Case 0: Same physical file or multi-document scan from same batch
        if meta_a.get("file_id") and meta_a["file_id"] == meta_b.get("file_id") and meta_a["file_id"] != "":
            # Check if they share business context or if they are separate independent invoices
            if meta_a["doc_num"] and meta_b["doc_num"] and meta_a["doc_num"] != meta_b["doc_num"]:
                # Two distinct invoices in one PDF -> belong to separate transactions unless cross-referenced
                pass
            else:
                return True, "exact_identifier", 0.99, {"reason": "Combined multi-document file scan", "file_id": meta_a["file_id"]}

        # Case 1: Filename shared transaction token (e.g. TXN-001)
        if meta_a["txn_token"] and meta_b["txn_token"] and meta_a["txn_token"] == meta_b["txn_token"]:
            return True, "exact_identifier", 1.00, {"matched_key": "TXN_TOKEN", "value": meta_a["txn_token"]}

        # Case 2: Exact PO Number match
        # Doc A is PO and Doc B references it, or Doc B is PO and Doc A references it
        if meta_a["doc_type"] == "PURCHASE_ORDER" and meta_a["doc_num"]:
            if meta_b["po_ref"] == meta_a["doc_num"] or meta_b["doc_num"] == meta_a["doc_num"]:
                return True, "exact_identifier", 1.00, {"matched_key": "PO_NUMBER", "value": meta_a["doc_num"]}
        if meta_b["doc_type"] == "PURCHASE_ORDER" and meta_b["doc_num"]:
            if meta_a["po_ref"] == meta_b["doc_num"] or meta_a["doc_num"] == meta_b["doc_num"]:
                return True, "exact_identifier", 1.00, {"matched_key": "PO_NUMBER", "value": meta_b["doc_num"]}
        if meta_a["po_ref"] and meta_b["po_ref"] and meta_a["po_ref"] == meta_b["po_ref"]:
            return True, "exact_identifier", 0.98, {"matched_key": "COMMON_PO_REF", "value": meta_a["po_ref"]}

        # Case 3: Exact Invoice Number match
        if meta_a["doc_num"] and (meta_b["inv_ref"] == meta_a["doc_num"] or (meta_a["doc_type"] == "INVOICE" and meta_b["doc_num"] == meta_a["doc_num"])):
            return True, "exact_identifier", 1.00, {"matched_key": "INVOICE_NUMBER", "value": meta_a["doc_num"]}
        if meta_b["doc_num"] and (meta_a["inv_ref"] == meta_b["doc_num"] or (meta_b["doc_type"] == "INVOICE" and meta_a["doc_num"] == meta_b["doc_num"])):
            return True, "exact_identifier", 1.00, {"matched_key": "INVOICE_NUMBER", "value": meta_b["doc_num"]}
        if meta_a["inv_ref"] and meta_b["inv_ref"] and meta_a["inv_ref"] == meta_b["inv_ref"]:
            return True, "exact_identifier", 0.98, {"matched_key": "COMMON_INVOICE_REF", "value": meta_a["inv_ref"]}

        # Case 4: Payment Reference match
        if meta_a["pay_ref"] and meta_b["pay_ref"] and meta_a["pay_ref"] == meta_b["pay_ref"]:
            return True, "exact_identifier", 0.99, {"matched_key": "PAYMENT_REFERENCE", "value": meta_a["pay_ref"]}

        # Case 5: Metadata Matching (Supplier + Customer + Amount)
        supplier_sim, supp_match = semantic_matcher.match_supplier(meta_a["supplier"], meta_b["supplier"])
        amt_match = False
        if meta_a["amount"] > 0 and meta_b["amount"] > 0:
            diff = abs(meta_a["amount"] - meta_b["amount"])
            if diff == 0:
                amt_match = True
            elif diff / max(meta_a["amount"], meta_b["amount"]) < 0.05:  # within 5%
                amt_match = True

        if supp_match and amt_match:
            return True, "metadata_match", 0.92, {
                "supplier_similarity": supplier_sim,
                "amount_a": str(meta_a["amount"]),
                "amount_b": str(meta_b["amount"])
            }

        # Case 6: Semantic similarity over line item descriptions + supplier match
        if supp_match and meta_a["items"] and meta_b["items"]:
            # Check item overlap
            aligned_items = semantic_matcher.align_line_items(meta_a["items"], meta_b["items"])
            strong_matches = [it for it in aligned_items if it.get("match_score", 0) >= 0.85]
            if len(strong_matches) >= 1:
                conf = 0.85 if len(strong_matches) == 1 else 0.90
                return True, "semantic_match", conf, {
                    "matched_items_count": len(strong_matches),
                    "supplier": meta_a["supplier"]
                }

        # Case 7: Hybrid multi-signal fusion
        if supplier_sim >= 0.75:
            # Partial signals combine
            score = supplier_sim * 0.5 + (0.4 if amt_match else 0.0)
            if score >= 0.70:
                return True, "hybrid", round(score, 2), {
                    "supplier_sim": supplier_sim,
                    "amt_match": amt_match
                }

        return False, "none", 0.0, {}

    @classmethod
    def group_documents_into_transactions(cls, documents: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Builds a multi-signal graph of documents and groups them into Transaction clusters.
        Returns:
            {
                canonical_ref: {
                    "documents": List[Dict],
                    "links": List[Dict[str, Any]] # edge list: {from_doc, to_doc, method, confidence, details}
                }
            }
        """
        if not documents:
            return {}

        metas = [cls.extract_document_identifiers(d) for d in documents]
        n = len(documents)

        # Adjacency matrix and edges
        adj = defaultdict(set)
        edges = []

        for i in range(n):
            for j in range(i + 1, n):
                is_linked, method, conf, details = cls.evaluate_pair_link(metas[i], metas[j])
                if is_linked and conf >= 0.70:
                    adj[i].add(j)
                    adj[j].add(i)
                    edges.append({
                        "from_doc_id": documents[i]["id"],
                        "to_doc_id": documents[j]["id"],
                        "from_idx": i,
                        "to_idx": j,
                        "link_method": method,
                        "link_confidence": conf,
                        "link_details": details
                    })

        # Connected components via BFS
        visited = set()
        clusters: Dict[str, Dict[str, Any]] = {}

        for i in range(n):
            if i not in visited:
                comp_indices = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp_indices.append(curr)
                    for nbr in adj[curr]:
                        if nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)

                comp_docs = [documents[idx] for idx in comp_indices]
                comp_metas = [metas[idx] for idx in comp_indices]

                # Determine canonical reference
                canonical_ref = None
                for m in comp_metas:
                    if m["po_ref"]:
                        canonical_ref = m["po_ref"]
                        break
                    if m["doc_type"] == "PURCHASE_ORDER" and m["doc_num"]:
                        canonical_ref = m["doc_num"]
                        break
                if not canonical_ref:
                    for m in comp_metas:
                        if m["txn_token"]:
                            canonical_ref = m["txn_token"]
                            break
                        if m["inv_ref"]:
                            canonical_ref = m["inv_ref"]
                            break
                        if m["doc_type"] == "INVOICE" and m["doc_num"]:
                            canonical_ref = m["doc_num"]
                            break
                if not canonical_ref:
                    first_num = comp_metas[0]["doc_num"]
                    canonical_ref = first_num or f"TXN-{comp_docs[0]['id'][:8].upper()}"

                # Filter edges relevant to this cluster
                comp_doc_ids = {d["id"] for d in comp_docs}
                cluster_edges = [
                    e for e in edges
                    if e["from_doc_id"] in comp_doc_ids and e["to_doc_id"] in comp_doc_ids
                ]

                clusters[canonical_ref] = {
                    "documents": comp_docs,
                    "edges": cluster_edges
                }

        return clusters

    @classmethod
    def link_database_documents(cls, db) -> List[Any]:
        """
        Scans all documents in DB, links them into Transaction clusters,
        and saves explicit TransactionDocument link entities with provenance.
        """
        from app.models.document import Document, TransactionDocument
        from app.models.transaction import Transaction

        docs = db.query(Document).all()
        if not docs:
            return []

        doc_dicts = [
            {
                "id": d.id,
                "file_id": getattr(d, "file_id", None),
                "filename": d.filename or "",
                "doc_type": getattr(d, "doc_type", "OTHER") or "OTHER",
                "document_type": getattr(d, "document_type", "OTHER") or "OTHER",
                "page_start": getattr(d, "page_start", 1) or 1,
                "page_end": getattr(d, "page_end", 1) or 1,
                "parsed_data": d.parsed_data or d.structured_data or {},
                "raw_text": d.raw_text or d.extracted_text or "",
                "orm_doc": d
            }
            for d in docs
        ]

        clusters = cls.group_documents_into_transactions(doc_dicts)

        for ref_key, cluster_info in clusters.items():
            cluster_docs = cluster_info["documents"]
            cluster_edges = cluster_info["edges"]

            # Skip single isolated unknown documents with zero financial data
            if len(cluster_docs) == 1:
                cd0 = cluster_docs[0]
                p0 = cd0.get("parsed_data", {})
                gt0 = float(p0.get("grand_total") or p0.get("payment_amount") or 0.0)
                if cd0.get("document_type") == "OTHER" and gt0 == 0.0 and not p0.get("document_number"):
                    continue

            # Find or create Transaction
            existing_txn = db.query(Transaction).filter(
                (Transaction.transaction_reference == ref_key) | (Transaction.transaction_ref == ref_key)
            ).first()

            supplier = ""
            customer = ""
            total_amt = 0.0
            txn_date = None

            for cd in cluster_docs:
                p = cd.get("parsed_data", {})
                if not supplier and p.get("supplier_name"):
                    supplier = p.get("supplier_name")
                if not customer and p.get("customer_name"):
                    customer = p.get("customer_name")
                if not txn_date and p.get("document_date"):
                    try:
                        txn_date = datetime.strptime(p.get("document_date")[:10], "%Y-%m-%d")
                    except Exception:
                        pass
                gt = float(p.get("grand_total") or p.get("payment_amount") or 0.0)
                if gt > total_amt:
                    total_amt = gt

            if not existing_txn:
                txn_id = f"txn_{uuid.uuid4().hex[:10]}"
                txn = Transaction(
                    id=txn_id,
                    transaction_reference=ref_key,
                    transaction_ref=ref_key,  # backward compatibility
                    title=f"Transaction {ref_key} ({supplier or 'MSME'})",
                    supplier=supplier,
                    supplier_name=supplier,  # backward compatibility
                    customer=customer,
                    customer_name=customer,  # backward compatibility
                    transaction_date=txn_date,
                    currency="INR",
                    total_amount=total_amt,
                    status="PENDING",
                    reconciliation_status="PENDING"
                )
                db.add(txn)
                db.flush()
                target_txn = txn
            else:
                target_txn = existing_txn
                target_txn.transaction_reference = ref_key
                if total_amt > target_txn.total_amount:
                    target_txn.total_amount = total_amt
                if supplier and not target_txn.supplier:
                    target_txn.supplier = supplier
                    target_txn.supplier_name = supplier

            # Link documents to Transaction & create TransactionDocument links
            for cd in cluster_docs:
                orm_d = cd["orm_doc"]
                if orm_d not in target_txn.documents:
                    target_txn.documents.append(orm_d)

                # Find edge info for this document
                doc_edge = next(
                    (e for e in cluster_edges if e["from_doc_id"] == orm_d.id or e["to_doc_id"] == orm_d.id),
                    None
                )
                method = doc_edge["link_method"] if doc_edge else "exact_identifier"
                conf = doc_edge["link_confidence"] if doc_edge else 1.0
                details = doc_edge["link_details"] if doc_edge else {"note": "Primary transaction document"}

                # Check if TransactionDocument link already exists
                existing_link = db.query(TransactionDocument).filter(
                    TransactionDocument.transaction_id == target_txn.id,
                    TransactionDocument.document_id == orm_d.id
                ).first()

                if not existing_link:
                    link_rec = TransactionDocument(
                        id=f"td_{uuid.uuid4().hex[:10]}",
                        transaction_id=target_txn.id,
                        document_id=orm_d.id,
                        link_method=method,
                        link_confidence=conf,
                        confirmed=False,
                        link_details=details
                    )
                    db.add(link_rec)

        db.commit()
        return db.query(Transaction).all()

    @classmethod
    def get_transaction_graph(cls, transaction_id: str, db) -> Dict[str, Any]:
        """
        Returns graph nodes (documents) and edges (provenance links) for visual display.
        """
        from app.models.transaction import Transaction
        from app.models.document import TransactionDocument

        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            return {"nodes": [], "edges": []}

        nodes = []
        for d in txn.documents:
            p_data = d.parsed_data or d.structured_data or {}
            nodes.append({
                "id": d.id,
                "document_type": d.document_type or d.doc_type,
                "document_number": d.document_number or p_data.get("document_number") or d.filename,
                "filename": d.filename,
                "page_start": d.page_start,
                "page_end": d.page_end,
                "confidence": d.confidence or d.classification_confidence,
                "total_amount": float(p_data.get("grand_total") or p_data.get("payment_amount") or 0.0),
                "date": p_data.get("document_date")
            })

        links = db.query(TransactionDocument).filter(
            TransactionDocument.transaction_id == transaction_id
        ).all()

        edges = []
        # Connect documents in graph
        for link in links:
            edges.append({
                "id": link.id,
                "transaction_id": link.transaction_id,
                "document_id": link.document_id,
                "link_method": link.link_method,
                "link_confidence": link.link_confidence,
                "confirmed": link.confirmed,
                "link_details": link.link_details
            })

        return {
            "transaction_id": txn.id,
            "transaction_reference": txn.transaction_reference or txn.transaction_ref,
            "nodes": nodes,
            "edges": edges
        }

transaction_linker = TransactionLinker()
