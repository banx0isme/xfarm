import os
import json
import argparse
import requests
from dotenv import load_dotenv

def _get_base_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_env(base_dir: str) -> None:
    load_dotenv(os.path.join(base_dir, ".env"))

def search_brave(query, count=5):
    _load_env(_get_base_dir())
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    
    if not api_key:
        print("Error: BRAVE_SEARCH_API_KEY not found in environment")
        return None
        
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": query,
        "count": count
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract just the top web results
        results = []
        if "web" in data and "results" in data["web"]:
            for item in data["web"]["results"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "description": item.get("description")
                })
                
        return results
    except Exception as e:
        print(f"Error querying Brave Search: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brave Web Search Tool")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--count", type=int, default=5, help="Number of results to return")
    
    args = parser.parse_args()
    
    results = search_brave(args.query, count=args.count)
    if results is not None:
        print(json.dumps(results, indent=2, ensure_ascii=False))
