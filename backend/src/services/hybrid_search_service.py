#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid search: vector recall + weighted rerank for similar historical cases.

Stage 1: Vector retrieval from historical_cases_vectors (top_k=100).
Stage 2: Weighted similarity rerank using HistoricalCaseMatcher._calculate_similarity.
"""
from typing import Dict, Any, List, Optional

from src.core.vector_store import SurrealDBSyncClient


def _vector_record_to_historical_case(rec: dict) -> dict:
    """Map vector store record to historical case dict for scoring."""
    return {
        "C_case_number": rec.get("case_number") or "",
        "H_location": rec.get("location") or "",
        "G_slope_no": rec.get("slope_no") or "",
        "J_subject_matter": "",
        "E_caller_name": "",
        "F_contact_no": "",
    }


def _vector_record_to_case_response(rec: dict) -> dict:
    """Map vector store record to API response case shape."""
    source = rec.get("source") or ""
    data_source = "Slopes Complaints 2021" if "slopes" in source else "SRR Data 2021-2024"
    return {
        "A_date_received": "",
        "C_case_number": rec.get("case_number") or "",
        "B_source": rec.get("source") or "",
        "G_slope_no": rec.get("slope_no") or "",
        "H_location": rec.get("location") or "",
        "I_nature_of_request": (rec.get("content") or "")[:500],
        "J_subject_matter": "",
        "data_source": data_source,
    }


class HybridSearchService:
    """Hybrid search: vector recall + weighted rerank."""

    def __init__(self, vector_client: SurrealDBSyncClient, weight_matcher):
        self.vector_client = vector_client
        self.weight_matcher = weight_matcher

    def _build_search_text(self, current_case: dict) -> str:
        """Build text for vector query from current case."""
        parts = [
            current_case.get("H_location") or "",
            current_case.get("G_slope_no") or "",
            current_case.get("J_subject_matter") or "",
            current_case.get("I_nature_of_request") or "",
            current_case.get("E_caller_name") or "",
        ]
        return " ".join(p for p in parts if p).strip() or "case"

    async def find_similar_cases(
        self,
        current_case: dict,
        limit: int = 10,
        min_similarity: float = 0.3,
        vector_top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical cases: vector recall then weighted rerank.

        Args:
            current_case: Current case dict (e.g. H_location, G_slope_no, J_subject_matter).
            limit: Max results to return.
            min_similarity: Minimum weighted score to include.
            vector_top_k: Number of candidates to retrieve from vector store for rerank.

        Returns:
            List of dicts: case, similarity_score, is_potential_duplicate, match_details, data_source.
        """
        search_text = self._build_search_text(current_case)
        candidates = await self.vector_client.retrieve_from_collection(
            SurrealDBSyncClient.COLLECTION_HISTORICAL_CASES,
            search_text,
            top_k=vector_top_k,
            filters=None,
        )
        if not candidates:
            return []

        # Get current case number for filtering
        current_case_number = current_case.get('C_case_number', '').strip()

        scored = []
        for c in candidates:
            historical_for_score = _vector_record_to_historical_case(c)
            
            # Skip if same case number (same case, not similar case)
            hist_case_number = historical_for_score.get('C_case_number', '').strip()
            if current_case_number and hist_case_number and \
               current_case_number == hist_case_number:
                continue
            
            score, details = self.weight_matcher._calculate_similarity(
                current_case, historical_for_score
            )
            if score < min_similarity:
                continue
            case_response = _vector_record_to_case_response(c)
            scored.append({
                "case": case_response,
                "similarity_score": score,
                "is_potential_duplicate": score >= 0.70,
                "match_details": details,
                "data_source": case_response.get("data_source", "historical"),
            })
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]


_hybrid_service: Optional[HybridSearchService] = None


def init_hybrid_search_service(vector_client: SurrealDBSyncClient, weight_matcher) -> None:
    """Initialize the global hybrid search service."""
    global _hybrid_service
    _hybrid_service = HybridSearchService(vector_client, weight_matcher)


def get_hybrid_search_service() -> HybridSearchService:
    """Get the global hybrid search service. Must call init_hybrid_search_service first."""
    if _hybrid_service is None:
        raise RuntimeError(
            "Hybrid search service not initialized. Call init_hybrid_search_service() first."
        )
    return _hybrid_service
