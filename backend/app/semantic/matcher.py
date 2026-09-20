"""
TRACE - Semantic Entity Matcher
Provides fuzzy semantic alignment for suppliers, customers, and line items.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from app.semantic.embeddings import embedding_service
from app.core.config import settings
from app.extraction.normalizer import clean_item_description, clean_entity_name

class SemanticMatcher:
    @staticmethod
    def match_supplier(name_a: Optional[str], name_b: Optional[str]) -> Tuple[float, bool]:
        if not name_a or not name_b:
            return 0.0, False
        
        ca = clean_entity_name(name_a)
        cb = clean_entity_name(name_b)
        if ca and cb and ca.lower() == cb.lower():
            return 1.0, True

        emb_sim = embedding_service.compute_similarity(ca or name_a, cb or name_b)

        # Token set overlap & containment
        toks_a = set(re.findall(r"\w+", (ca or name_a).lower()))
        toks_b = set(re.findall(r"\w+", (cb or name_b).lower()))
        if toks_a and toks_b:
            inter = len(toks_a & toks_b)
            union = len(toks_a | toks_b)
            jaccard = inter / union if union > 0 else 0.0
            containment = inter / min(len(toks_a), len(toks_b)) if min(len(toks_a), len(toks_b)) > 0 else 0.0
            token_score = max(jaccard, 0.95 * containment if inter > 0 else 0.0)
            similarity = max(emb_sim, token_score, 0.5 * (emb_sim + token_score))
        else:
            similarity = emb_sim

        is_match = similarity >= settings.SUPPLIER_MATCH_THRESHOLD
        return round(similarity, 4), is_match

    @staticmethod
    def match_customer(name_a: Optional[str], name_b: Optional[str]) -> Tuple[float, bool]:
        return SemanticMatcher.match_supplier(name_a, name_b)

    @staticmethod
    def match_item(desc_a: str, desc_b: str) -> Tuple[float, bool]:
        if not desc_a or not desc_b:
            return 0.0, False
        ca = clean_item_description(desc_a)
        cb = clean_item_description(desc_b)
        if ca.lower() == cb.lower():
            return 1.0, True

        similarity = embedding_service.compute_similarity(ca, cb)
        is_match = similarity >= settings.ITEM_MATCH_THRESHOLD
        return round(similarity, 4), is_match

    @staticmethod
    def align_line_items(
        po_items: List[Dict[str, Any]],
        invoice_items: List[Dict[str, Any]],
        delivery_items: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Aligns line items across Purchase Order, Invoice, and Delivery Note.
        Returns a list of aligned item tuples:
        [
            {
                "item_key": str,
                "po_item": Optional[Dict],
                "invoice_item": Optional[Dict],
                "delivery_item": Optional[Dict],
                "match_score": float
            }
        ]
        """
        delivery_items = delivery_items or []
        aligned = []
        used_inv_indices = set()
        used_dn_indices = set()

        # Step 1: Match PO items against Invoice and Delivery items
        for p_idx, po_it in enumerate(po_items):
            po_desc = clean_item_description(po_it.get("normalized_description") or po_it.get("description", ""))
            
            best_inv_idx = -1
            best_inv_sim = 0.0
            for i_idx, inv_it in enumerate(invoice_items):
                if i_idx in used_inv_indices:
                    continue
                inv_desc = clean_item_description(inv_it.get("normalized_description") or inv_it.get("description", ""))
                sim, is_match = SemanticMatcher.match_item(po_desc, inv_desc)
                if is_match and sim > best_inv_sim:
                    best_inv_sim = sim
                    best_inv_idx = i_idx

            matched_inv = None
            if best_inv_idx >= 0:
                matched_inv = invoice_items[best_inv_idx]
                used_inv_indices.add(best_inv_idx)

            # Match with Delivery note items
            best_dn_idx = -1
            best_dn_sim = 0.0
            for d_idx, dn_it in enumerate(delivery_items):
                if d_idx in used_dn_indices:
                    continue
                dn_desc = clean_item_description(dn_it.get("normalized_description") or dn_it.get("description", ""))
                sim, is_match = SemanticMatcher.match_item(po_desc, dn_desc)
                if is_match and sim > best_dn_sim:
                    best_dn_sim = sim
                    best_dn_idx = d_idx

            matched_dn = None
            if best_dn_idx >= 0:
                matched_dn = delivery_items[best_dn_idx]
                used_dn_indices.add(best_dn_idx)

            match_score = max(best_inv_sim, best_dn_sim) if (matched_inv or matched_dn) else 1.0
            aligned.append({
                "item_key": po_desc,
                "po_item": po_it,
                "invoice_item": matched_inv,
                "delivery_item": matched_dn,
                "match_score": match_score
            })

        # Step 2: Handle remaining unaligned Invoice items (e.g. unbilled items on PO)
        for i_idx, inv_it in enumerate(invoice_items):
            if i_idx not in used_inv_indices:
                inv_desc = inv_it.get("normalized_description") or inv_it.get("description", "")
                aligned.append({
                    "item_key": inv_desc,
                    "po_item": None,
                    "invoice_item": inv_it,
                    "delivery_item": None,
                    "match_score": 0.0
                })

        # Step 3: Handle remaining unaligned Delivery items
        for d_idx, dn_it in enumerate(delivery_items):
            if d_idx not in used_dn_indices:
                dn_desc = dn_it.get("normalized_description") or dn_it.get("description", "")
                aligned.append({
                    "item_key": dn_desc,
                    "po_item": None,
                    "invoice_item": None,
                    "delivery_item": dn_it,
                    "match_score": 0.0
                })

        return aligned

semantic_matcher = SemanticMatcher()
