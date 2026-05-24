import time
import concurrent.futures
import sys
import os

# Ensure the parent directory is in the path so we can import the extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from edgar_extractor import get_cik_from_ticker

# A list of 20 random tickers to bombard the SEC API with
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "ADBE", "CRM",
    "INTC", "AMD", "CSCO", "PEP", "KO", "DIS", "CMCSA", "VZ", "T", "PFE"
]
USER_AGENT = {"User-Agent": "Engineering_Portfolio_Benchmark contact@yourdomain.com"}

def worker(ticker):
    """Worker function to fetch a CIK"""
    # This calls the SEC API, triggering the rate limiter
    cik = get_cik_from_ticker(ticker, USER_AGENT)
    print(f"Resolved {ticker} -> {cik}")

if __name__ == "__main__":
    print("🚀 Starting Concurrent Ingestion Stress Test...")
    print("Target: SEC EDGAR API (Strict Limit: 10 req/sec)")
    print("Executing 20 concurrent requests using ThreadPoolExecutor...\n")
    
    start_time = time.time()
    
    # Launch 20 threads simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(worker, TICKERS)
        
    end_time = time.time()
    elapsed = end_time - start_time
    
    print("\n📊 BENCHMARK RESULTS")
    print("-" * 30)
    print(f"Total Requests Processed: {len(TICKERS)}")
    print(f"Total Execution Time:     {elapsed:.2f} seconds")
    print(f"Average Rate:             {len(TICKERS) / elapsed:.2f} req/sec")
    
    if elapsed >= 2.0:
        print("\n✅ STATUS: SUCCESS - Token Bucket successfully throttled requests to comply with SEC limits.")
    else:
        print("\n❌ STATUS: FAILED - Executed too fast. Rate limit breach detected.")