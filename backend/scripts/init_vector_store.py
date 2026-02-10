#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize vector store with historical cases, tree inventory, and knowledge docs.

Run from project root:
  python -m backend.scripts.init_vector_store

Or from backend directory:
  python -m scripts.init_vector_store
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure backend is on path for config and src imports
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import pandas as pd
import chardet

from config.settings import SURREALDB_PERSIST_PATH
from src.core.vector_store import SurrealDBSyncClient
from src.services.embedding_service import generate_embedding

# Batch size for embedding and insert to avoid memory and API overload
EMBED_BATCH_SIZE = 50

DATA_DIR = _backend_dir / "data"
DOCS_TEMPLATES_DIR = _backend_dir.parent / "docs" / "templates"
SLOPES_FILENAME = "Slopes Complaints & Enquires Under             TC K928   4-10-2021.xlsx"
SRR_FILENAME = "SRR data 2021-2024.csv"
TREE_FILENAME = "Tree inventory.xlsx"


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _safe_get(row, *keys) -> str:
    for k in keys:
        try:
            v = row.get(k)
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                return str(v).strip()
        except Exception:
            pass
    return ""


async def vectorize_historical_cases(client: SurrealDBSyncClient) -> int:
    """Vectorize historical cases from Slopes 2021 Excel and SRR 2021-2024 CSV."""
    total = 0

    # --- Slopes Complaints 2021 ---
    slopes_path = DATA_DIR / SLOPES_FILENAME
    if slopes_path.exists():
        df = pd.read_excel(slopes_path)
        df = df.dropna(how="all")
        key_cols = ["Received \nDate", "Case No. ", "Venue", "District"]
        existing = [c for c in key_cols if c in df.columns]
        if existing:
            df = df.dropna(subset=existing, how="all")
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

        texts = []
        meta = []
        for idx, row in df.iterrows():
            case_no = _safe_get(row, "Case No. ")
            date_val = _safe_get(row, "Received \nDate")
            venue = _safe_get(row, "Venue")
            district = _safe_get(row, "District")
            location = venue or district
            slope_no = _safe_get(row, "Verified Slope No.") or _safe_get(row, "Slope no")
            nature = _safe_get(row, "Nature of complaint")
            subject = _safe_get(row, "AIMS Complaint Type")
            remarks = _safe_get(row, "Remarks")
            content = (
                f"Case {case_no}. Date: {date_val}. Location: {location}. Slope: {slope_no}. "
                f"Subject: {subject}. Nature: {nature}. Remarks: {remarks}"
            )
            texts.append(content[:2000])
            meta.append({
                "case_id": f"slopes_2021_{idx}",
                "case_number": case_no,
                "location": location,
                "slope_no": slope_no,
                "source": "slopes_2021",
            })

        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch_texts = texts[i : i + EMBED_BATCH_SIZE]
            batch_meta = meta[i : i + EMBED_BATCH_SIZE]
            embeddings = generate_embedding(batch_texts)
            for j, (m, vec) in enumerate(zip(batch_meta, embeddings)):
                rec = {
                    **m,
                    "content": batch_texts[j],
                    "vector": vec,
                }
                await client.add_to_collection(client.COLLECTION_HISTORICAL_CASES, rec)
                total += 1
            print(f"  Slopes 2021: {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)}")

    # --- SRR Data 2021-2024 ---
    srr_path = DATA_DIR / SRR_FILENAME
    if srr_path.exists():
        with open(srr_path, "rb") as f:
            enc = chardet.detect(f.read()).get("encoding") or "utf-8"
        df = pd.read_csv(srr_path, encoding=enc)
        df = df.dropna(how="all")
        key_cols = ["Received \nDate", "Received Date", "Source", "District"]
        existing = [c for c in key_cols if c in df.columns]
        if existing:
            df = df.dropna(subset=existing, how="all")

        texts = []
        meta = []
        for idx, row in df.iterrows():
            case_no = _safe_get(row, "Case No.", "Case No. ")
            date_val = _safe_get(row, "Received Date", "Received \nDate")
            venue = _safe_get(row, "Venue")
            district = _safe_get(row, "District")
            location = venue or district
            slope_no = _safe_get(row, "Verified Slope No.") or _safe_get(row, "Slope No.\n")
            inquiry = _safe_get(row, "Inquiry")
            subject = _safe_get(row, "Subject Matter")
            content = (
                f"Case {case_no}. Date: {date_val}. Location: {location}. Slope: {slope_no}. "
                f"Subject: {subject}. Inquiry: {inquiry}"
            )
            texts.append(content[:2000])
            meta.append({
                "case_id": f"srr_2021_2024_{idx}",
                "case_number": case_no,
                "location": location,
                "slope_no": slope_no,
                "source": "srr_2021_2024",
            })

        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch_texts = texts[i : i + EMBED_BATCH_SIZE]
            batch_meta = meta[i : i + EMBED_BATCH_SIZE]
            embeddings = generate_embedding(batch_texts)
            for j, (m, vec) in enumerate(zip(batch_meta, embeddings)):
                rec = {
                    **m,
                    "content": batch_texts[j],
                    "vector": vec,
                }
                await client.add_to_collection(client.COLLECTION_HISTORICAL_CASES, rec)
                total += 1
            print(f"  SRR 2021-2024: {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)}")

    return total


async def vectorize_tree_inventory(client: SurrealDBSyncClient) -> int:
    """Vectorize tree inventory from Tree inventory.xlsx."""
    total = 0
    tree_path = DATA_DIR / TREE_FILENAME
    if not tree_path.exists():
        return 0

    df = pd.read_excel(tree_path)
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    texts = []
    meta = []
    for idx, row in df.iterrows():
        tree_id = _safe_get(row, "Tree ID")
        slope_no = _safe_get(row, "Slope No.")
        species = _safe_get(row, "Species")
        location = _safe_get(row, "Location", "Venue", "District")
        dbh = _safe_get(row, "DBH")
        height = _safe_get(row, "Height")
        condition = _safe_get(row, "Condition")
        content = (
            f"Tree ID {tree_id}. Slope: {slope_no}. Species: {species}. "
            f"Location: {location}. DBH: {dbh}. Height: {height}. Condition: {condition}"
        )
        texts.append(content[:2000])
        meta.append({
            "tree_id": tree_id,
            "slope_no": slope_no,
            "species": species,
            "location": location,
        })

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch_texts = texts[i : i + EMBED_BATCH_SIZE]
        batch_meta = meta[i : i + EMBED_BATCH_SIZE]
        embeddings = generate_embedding(batch_texts)
        for j, (m, vec) in enumerate(zip(batch_meta, embeddings)):
            rec = {
                **m,
                "content": batch_texts[j],
                "vector": vec,
            }
            await client.add_to_collection(client.COLLECTION_TREE_INVENTORY, rec)
            total += 1
        print(f"  Tree inventory: {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)}")

    return total


async def vectorize_knowledge_docs(client: SurrealDBSyncClient) -> int:
    """Vectorize knowledge docs from docs/templates (e.g. .docx)."""
    total = 0
    if not DOCS_TEMPLATES_DIR.exists():
        return 0

    try:
        from src.utils.file_processors import process_word
    except Exception:
        try:
            from docx import Document
            def process_word(path):
                doc = Document(path)
                return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            print("  Skipping knowledge docs: no docx support")
            return 0

    for path in sorted(DOCS_TEMPLATES_DIR.iterdir()):
        if path.suffix.lower() != ".docx":
            continue
        try:
            text = process_word(str(path))
            if not text or len(text.strip()) < 10:
                continue
            text = text.strip()[:8000]
            embeddings = generate_embedding([text])
            doc_type = "template"
            if "interim" in path.name.lower():
                doc_type = "interim_reply"
            elif "final" in path.name.lower():
                doc_type = "final_reply"
            elif "wrong" in path.name.lower():
                doc_type = "wrong_referral_reply"
            rec = {
                "doc_type": doc_type,
                "filename": path.name,
                "content": text,
                "vector": embeddings[0],
            }
            await client.add_to_collection(client.COLLECTION_KNOWLEDGE_DOCS, rec)
            total += 1
            print(f"  Knowledge doc: {path.name}")
        except Exception as e:
            print(f"  Error processing {path.name}: {e}")

    return total


async def main():
    print("Initializing vector store...")
    client = SurrealDBSyncClient(SURREALDB_PERSIST_PATH)

    print("Vectorizing historical cases...")
    n_cases = await vectorize_historical_cases(client)
    print(f"  Done: {n_cases} historical cases")

    print("Vectorizing tree inventory...")
    n_trees = await vectorize_tree_inventory(client)
    print(f"  Done: {n_trees} tree records")

    print("Vectorizing knowledge docs...")
    n_docs = await vectorize_knowledge_docs(client)
    print(f"  Done: {n_docs} knowledge docs")

    print("Vectorization complete.")
    print(f"  Total: {n_cases} cases, {n_trees} trees, {n_docs} docs.")


if __name__ == "__main__":
    asyncio.run(main())
