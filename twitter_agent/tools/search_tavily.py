import os
import json
import argparse
from dotenv import load_dotenv
from tavily import TavilyClient

def _get_base_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_env(base_dir: str) -> None:
    load_dotenv(os.path.join(base_dir, ".env"))

def search_tavily(query, search_depth="advanced", max_results=5):
    _load_env(_get_base_dir())
    api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        print("Error: TAVILY_API_KEY not found in environment")
        return None
        
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query, 
            search_depth=search_depth,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )
        return response
    except Exception as e:
        print(f"Error querying Tavily: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tavily Deep Search Tool")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--depth", type=str, default="advanced", choices=["basic", "advanced"], help="Search depth")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of results to return")
    
    args = parser.parse_args()
    
    results = search_tavily(args.query, args.depth, max_results=args.max_results)
    if results:
        print(json.dumps(results, indent=2, ensure_ascii=False))
