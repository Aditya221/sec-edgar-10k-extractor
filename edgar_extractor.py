import requests
import re
import time
import threading
from html.parser import HTMLParser
from typing import Dict, Any, Optional

class TokenBucketRateLimiter:
    """
    Enterprise-grade Token Bucket Rate Limiter.
    Ensures strict compliance with SEC's 10 requests/second limit.
    Thread-safe for concurrent ingestion workers.
    """
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.timestamp
            self._tokens = min(self.capacity, self._tokens + elapsed * self.fill_rate)
            self.timestamp = now
            
            if self._tokens < tokens:
                deficit = tokens - self._tokens
                wait_time = deficit / self.fill_rate
                time.sleep(wait_time)
                # Reset timestamp after sleeping
                self._tokens = 0.0
                self.timestamp = time.monotonic()
            else:
                self._tokens -= tokens

# Global SEC limiter: Max 10 requests per second
sec_limiter = TokenBucketRateLimiter(capacity=10, fill_rate=10.0)


class SECHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_accumulator = []
        self.ignore_tag = False

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style", "table"]:
            self.ignore_tag = True

    def handle_endtag(self, tag):
        if tag in ["script", "style", "table"]:
            self.ignore_tag = False

    def handle_data(self, data):
        if not self.ignore_tag and data.strip():
            self.text_accumulator.append(data.strip())

    def get_clean_text(self) -> str:
        return " ".join(self.text_accumulator)


def get_cik_from_ticker(ticker: str, headers: dict) -> str:
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        sec_limiter.consume(1) # Rate limit applied
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for key, value in data.items():
                if value.get("ticker") == ticker.upper():
                    return str(value.get("cik_str")).zfill(10)
    except Exception as e:
        print(f"Ticker Resolution Error: {e}")
    return ""


def fetch_mda_content(cik: str, cleaned_adsh: str, identity_headers: dict) -> str:
    stripped_cik = cik.lstrip("0")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{stripped_cik}/{cleaned_adsh}/index.json"
    
    try:
        sec_limiter.consume(1) # Rate limit applied
        response = requests.get(index_url, headers=identity_headers, timeout=10)
        if response.status_code != 200:
            return ""
            
        directory_items = response.json().get("directory", {}).get("item", [])
        primary_document_name = next(
            (item.get("name") for item in directory_items if item.get("type") == "10-K" and item.get("name", "").endswith((".htm", ".html"))), 
            None
        )
                
        if not primary_document_name:
            return ""
            
        document_url = f"https://www.sec.gov/Archives/edgar/data/{stripped_cik}/{cleaned_adsh}/{primary_document_name}"
        
        sec_limiter.consume(1) # Rate limit applied
        doc_response = requests.get(document_url, headers=identity_headers, timeout=20)
        
        if doc_response.status_code != 200:
            return ""
            
        parser = SECHTMLTextExtractor()
        parser.feed(doc_response.text)
        full_text = parser.get_clean_text()
        
        matches = [m.start() for m in re.finditer(r"Item\s*7\.?\s*Management", full_text, re.IGNORECASE)]
        
        if len(matches) > 1:
            start_idx = matches[-1] 
            return full_text[start_idx : start_idx + 6000]
        elif matches:
            start_idx = matches[0]
            return full_text[start_idx : start_idx + 6000]
            
        return full_text[:6000] 
        
    except Exception as e:
        print(f"Extraction Error: {e}")
        return ""


def extract_10k_mda(ticker: str, user_agent_email: str) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": user_agent_email}
    exact_cik = get_cik_from_ticker(ticker, headers)
    if not exact_cik:
        return None

    search_url = "https://efts.sec.gov/LATEST/search-index"
    params = {"ciks": exact_cik, "forms": "10-K"}
    
    try:
        sec_limiter.consume(1) # Rate limit applied
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        hits = response.json().get("hits", {}).get("hits", [])
        if not hits:
            return None
            
        sorted_hits = sorted(hits, key=lambda x: x.get("_source", {}).get("file_date", ""), reverse=True)
        top_hit = sorted_hits[0]["_source"]
        
        company_name = top_hit.get("entity_name", ticker)
        adsh = str(top_hit.get("adsh", ""))
        cleaned_adsh = adsh.replace("-", "")
        
        mda_text = fetch_mda_content(exact_cik, cleaned_adsh, headers)

        return {
            "company": company_name,
            "filing_date": top_hit.get("file_date"),
            "source_url": f"https://www.sec.gov/Archives/edgar/data/{exact_cik.lstrip('0')}/{cleaned_adsh}/",
            "mda_excerpt": mda_text
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None