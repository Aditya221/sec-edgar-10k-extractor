import time
import concurrent.futures
import sys
import os
import threading

# Ensure the parent directory is in the path so we can import the extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from edgar_extractor import extract_10k_mda, sec_limiter

# 5 tickers, ~4 calls each = ~20 total requests
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
USER_AGENT_EMAIL = "21MarketingLabs adityavarma0111@gmail.com"

# Thread-safe request counter to measure exact rate limit compliance
request_count = 0
request_count_lock = threading.Lock()
original_consume = sec_limiter.consume

def patched_consume(tokens=1):
    global request_count
    with request_count_lock:
        request_count += tokens
    return original_consume(tokens)

# Monkeypatch the rate limiter's consume method to track all API requests
sec_limiter.consume = patched_consume

def worker(ticker):
    """Worker function to execute the full MD&A extraction pipeline"""
    try:
        result = extract_10k_mda(ticker, USER_AGENT_EMAIL)
        if result:
            print(f"✅ {ticker}: {result['company']} — {len(result['mda_excerpt'])} chars extracted")
        else:
            print(f"❌ {ticker}: No result returned")
    except Exception as e:
        print(f"❌ {ticker}: Exception occurred: {e}")

if __name__ == "__main__":
    print("🚀 Starting Concurrent Ingestion Stress Test...")
    print("Target: SEC EDGAR API (Strict Limit: 10 req/sec)")
    print("Executing full 10-K extraction pipeline for 5 tickers concurrently...\n")
    
    start_time = time.time()
    
    # Launch concurrent threads for all tickers
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TICKERS)) as executor:
        executor.map(worker, TICKERS)
        
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Calculate average rate based on ACTUAL requests made
    average_rate = request_count / elapsed if elapsed > 0 else 0
    
    print("\n📊 BENCHMARK RESULTS")
    print("-" * 30)
    print(f"Total Tickers Processed:  {len(TICKERS)}")
    print(f"Total API Requests Made:  {request_count}")
    print(f"Total Execution Time:     {elapsed:.2f} seconds")
    
    if average_rate <= 10.5:  # 10% tolerance for timing variance
        print(f"📊 Average rate: {average_rate:.1f} req/sec (limit: 10) ✅")
    else:
        print(f"📊 Average rate: {average_rate:.1f} req/sec (limit: 10) ❌")