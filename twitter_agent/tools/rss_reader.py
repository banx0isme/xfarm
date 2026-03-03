import json
import os
import feedparser
from datetime import datetime, timezone
from dateutil import parser as date_parser

def load_feeds(config_path="feeds.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {config_path}: {e}")
        return []

def parse_feed(feed_info):
    url = feed_info.get("url")
    name = feed_info.get("name")
    
    print(f"Parsing feed: {name} ({url})")
    parsed = feedparser.parse(url)
    
    entries = []
    
    for entry in parsed.entries[:10]: # Top 10 newest
        try:
            pub_date = entry.get("published") or entry.get("updated")
            if pub_date:
                dt = date_parser.parse(pub_date)
            else:
                dt = datetime.now(timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
            
        entries.append({
            "source": name,
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "published_at": dt.isoformat(),
            "summary": entry.get("summary", "").strip()[:500] # Limit summary length
        })
        
    return entries

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "feeds.json")
    
    feeds = load_feeds(config_path)
    all_news = []
    
    for feed in feeds:
        news = parse_feed(feed)
        all_news.extend(news)
        
    # Sort by published date descending
    all_news.sort(key=lambda x: x["published_at"], reverse=True)
    
    output = json.dumps(all_news[:20], indent=2, ensure_ascii=False)
    print(output)
    
    return all_news

if __name__ == "__main__":
    main()
