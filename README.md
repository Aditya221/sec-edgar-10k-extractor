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
1. **Entity Resolution:** Maps a standard corporate domain (e.g., `apple.com`) or ticker to its Central Index Key (CIK) via the public EDGAR submissions API.
2. **Defensive Routing:** Implements strict type-checking to intercept array-nested identifiers before they trigger `TypeErrors` during regex processing.
3. **Native Sorting:** Replaces HTTP query-string sorting with a native Python-side array sort to guarantee the retrieval of the absolute most recent filing without triggering HTTP 400 syntax errors.
4. **HTML Tokenization:** Uses a custom `HTMLParser` class to stream and strip heavy markup, isolating the pure text.
5. **Heuristic Disambiguation:** Skips ToC false positives to reliably land on the true MD&A body.

## 📊 Thread-Safe Throttling & Concurrent Ingestion
The SEC EDGAR system enforces a strict rate limit of **10 requests per second**. Exceeding this limit results in immediate IP blocks and broken ingestion pipelines. 

To handle high-throughput corporate ingestion, this architecture implements a highly defensive, thread-safe rate-limiting system designed for concurrent workers:

### Technical Architecture
- **Token Bucket Algorithm:** Implements a mathematical Token Bucket rate limiter that strictly controls API access.
- **Thread Safety:** Uses a synchronized `threading.Lock()` to safely coordinate token consumption across multiple concurrent worker threads.
- **Monotonic Timing:** Relies on `time.monotonic()` instead of the system clock to calculate token replenishment, ensuring the limiter remains immune to system clock drift, network time adjustments (NTP), or daylight saving changes.
- **Non-Blocking / Throttling Sleep:** Dynamically calculates timing deficits and applies exact, minimal sleep intervals to throttle threads back into compliance without dropping requests.

### Stress Test & Benchmark
The benchmark executes the **entire** 10-K ingestion pipeline concurrently for 5 different public companies. Each pipeline run triggers approximately 4 underlying API requests (Ticker-to-CIK resolution, EFTS search lookup, directory index mapping, and document content extraction)—subjecting the gateway to **20 highly concurrent API requests** simultaneously.

Run the stress test using:
```bash
python3 benchmark/test_rate_limit.py
```

**Real Ingestion Log:**
```stdout
🚀 Starting Concurrent Ingestion Stress Test...
Target: SEC EDGAR API (Strict Limit: 10 req/sec)
Executing full 10-K extraction pipeline for 5 tickers concurrently...

✅ AAPL: Apple Inc. — 6000 chars extracted
✅ GOOGL: Alphabet Inc. — 6000 chars extracted
✅ AMZN: AMAZON COM INC — 6000 chars extracted
✅ TSLA: Tesla, Inc. — 6000 chars extracted
✅ MSFT: MICROSOFT CORP — 6000 chars extracted

📊 BENCHMARK RESULTS
------------------------------
Total Tickers Processed:  5
Total API Requests Made:  20
Total Execution Time:     5.29 seconds
📊 Average rate: 3.8 req/sec (limit: 10) ✅
```

## 🚀 Quick Start

### Installation
Minimal dependencies required.
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from edgar_extractor import extract_10k_mda

# Extract MD&A for Apple Inc.
result = extract_10k_mda("AAPL", "YourName yourname@domain.com")

if result:
    print(f"Company: {result['company']}")
    print(f"Filing Date: {result['filing_date']}")
    print(f"Source URL: {result['source_url']}")
    print(f"MD&A Excerpt:\n{result['mda_excerpt'][:300]}...")
```