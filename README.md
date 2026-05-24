# SEC EDGAR 10-K MD&A Extractor

A robust, zero-cost Python pipeline for extracting the Management's Discussion and Analysis (MD&A) section from SEC 10-K filings. 

Designed for enterprise AI ingestion, this extractor bypasses heavy XBRL markup, handles undocumented API type mutations, and resolves deep SEC directory structures to deliver clean, highly-dense corporate text ready for LLM vectorization.

## ⚠️ The Problem with Standard SEC Scraping
Harvesting financial narrative data for Retrieval-Augmented Generation (RAG) pipelines is notoriously difficult because:
1. **API Mutations:** The SEC EDGAR ElasticSearch backend frequently returns tracking identifiers (like `file_num` and `cik`) nested unpredictably inside arrays rather than standard string formats, breaking traditional parsing logic.
2. **URL Encoding Rejections:** The SEC's security gateway often rejects standard Python `requests` payloads containing structured JSON arrays (throwing HTTP 400s).
3. **XBRL Bloat:** Modern 10-K filings contain massive blocks of inline XBRL data and malformed HTML tables that exceed standard regex recursion limits and crash downstream embedding models.
4. **Table of Contents Traps:** Searching for "Item 7" usually hits the Table of Contents 3-4 times before hitting the actual business narrative.

## 🛠️ The Architectural Solution
This pipeline implements a deterministic, multi-phase extraction sequence:
1. **Entity Resolution:** Maps a standard corporate domain (e.g., `apple.com`) to its Central Index Key (CIK) via the public EDGAR submissions API.
2. **Defensive Routing:** Implements strict type-checking to intercept array-nested identifiers before they trigger `TypeErrors` during regex processing.
3. **Native Sorting:** Replaces HTTP query-string sorting with a native Python-side array sort to guarantee the retrieval of the absolute most recent filing without triggering HTTP 400 syntax errors.
4. **HTML Tokenization:** Uses a custom `HTMLParser` class to stream and strip heavy markup, isolating the pure text.
5. **Heuristic Disambiguation:** Skips ToC false positives to reliably land on the true MD&A body.

## 🚀 Quick Start

### Installation
Minimal dependencies required.
```bash
pip install -r requirements.txt