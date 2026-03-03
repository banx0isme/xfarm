import os
import json
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apify_client import ApifyClient

ACTOR_ID = "apidojo/tweet-scraper"

def get_influencers(file_path="influencers.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [str(item["handle"]) for item in data]
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def _get_base_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_apify_token(base_dir: str, apify_token: str | None = None) -> str | None:
    if apify_token:
        return apify_token
    load_dotenv(os.path.join(base_dir, ".env"))
    return os.getenv("APIFY_API_TOKEN")

def _normalize_tweet_item(item: dict, source_query: str | None = None) -> dict:
    favorites = item.get("favoriteCount", 0) or item.get("likeCount", 0) or item.get("favorites", 0)
    retweets = item.get("retweetCount", 0) or item.get("retweets", 0)

    author_info = item.get("author", {}) or {}
    author_name = (
        author_info.get("userName")
        or author_info.get("screen_name")
        or author_info.get("username")
        or item.get("user", {}).get("screen_name")
        or item.get("user", {}).get("username")
    )

    tweet_id = item.get("id") or item.get("id_str")
    text = item.get("text") or item.get("fullText") or item.get("full_text")
    created_at = item.get("createdAt") or item.get("created_at")
    url = item.get("url")

    normalized = {
        "id": tweet_id,
        "author": author_name,
        "text": text,
        "likes": favorites,
        "retweets": retweets,
        "created_at": created_at,
        "url": url,
    }
    if source_query:
        normalized["source_query"] = source_query
    return normalized

def _call_apify_for_query(
    client: ApifyClient,
    query: str,
    per_query_limit: int,
    max_total_charge_usd: float | None,
) -> list[dict]:
    run_input = {
        "searchTerms": [query],
        "searchMode": "live",
        # Different actors/versions use different names; set both for compatibility.
        "maxTweets": per_query_limit,
        "maxItems": per_query_limit,
    }

    call_kwargs = {"run_input": run_input}
    if max_total_charge_usd is not None:
        call_kwargs["max_total_charge_usd"] = max_total_charge_usd

    run = client.actor(ACTOR_ID).call(**call_kwargs)

    items: list[dict] = []
    count = 0
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
        count += 1
        if count >= per_query_limit:
            break
    return items

def _format_date(d) -> str:
    return d.strftime("%Y-%m-%d")

def _render_query_template(template: str, *, today, since, yesterday, tomorrow, fresh_since, fresh_until) -> str:
    return template.format(
        today=_format_date(today),
        yesterday=_format_date(yesterday),
        tomorrow=_format_date(tomorrow),
        since=_format_date(since),
        fresh_since=_format_date(fresh_since),
        fresh_until=_format_date(fresh_until),
    )

def build_default_operator_queries(
    topic: str,
    *,
    today=None,
    since_days: int = 5,
    fresh_days: int = 1,
    today_only: bool = False,
) -> dict[str, str]:
    if today is None:
        today = datetime.now().date()

    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    since = today - timedelta(days=since_days)
    fresh_since = today - timedelta(days=fresh_days)
    fresh_until = tomorrow

    base = topic.strip()

    templates = {
        "popular": f"{base} min_retweets:30 filter:media since:{{since}}",
        "viral": f"{base} min_retweets:100 min_faves:200 filter:media since:{{since}}",
        "fresh": f"{base} min_retweets:20 filter:media since:{{fresh_since}}",
        "video": f"{base} filter:videos min_faves:50 since:{{since}}",
        "gold": f"{base} min_retweets:30 min_faves:50 filter:media -filter:retweets since:{{since}}",
    }

    if today_only:
        templates["fresh"] = f"{base} min_retweets:20 filter:media since:{{today}} until:{{tomorrow}}"

    return {
        name: _render_query_template(
            tpl,
            today=today,
            since=since,
            yesterday=yesterday,
            tomorrow=tomorrow,
            fresh_since=fresh_since,
            fresh_until=fresh_until,
        )
        for name, tpl in templates.items()
    }

def scrape_operator_queries(
    *,
    topic: str = "Polymarket",
    since_days: int = 5,
    per_query_limit: int = 100,
    total_limit: int = 500,
    include: list[str] | None = None,
    queries: list[str] | None = None,
    today_only: bool = False,
    apify_token: str | None = None,
    max_total_charge_usd: float | None = 1.0,
    output_file: str | None = None,
):
    if per_query_limit > 100:
        raise ValueError("--per-query-limit must be <= 100")
    if total_limit > 500:
        raise ValueError("--total-limit must be <= 500")

    base_dir = _get_base_dir()
    resolved_token = _load_apify_token(base_dir, apify_token=apify_token)
    if not resolved_token:
        print("Error: APIFY_API_TOKEN is not set (env or twitter_agent/.env).")
        return None

    client = ApifyClient(resolved_token)

    if queries:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        since = today - timedelta(days=since_days)
        fresh_since = today - timedelta(days=1)
        fresh_until = tomorrow
        rendered_queries = [
            _render_query_template(
                q,
                today=today,
                since=since,
                yesterday=yesterday,
                tomorrow=tomorrow,
                fresh_since=fresh_since,
                fresh_until=fresh_until,
            )
            for q in queries
        ]
        selected_queries = [(f"custom_{i+1}", q) for i, q in enumerate(rendered_queries)]
    else:
        default_queries = build_default_operator_queries(
            topic,
            since_days=since_days,
            today_only=today_only,
        )
        names = include or list(default_queries.keys())
        selected_queries = [(name, default_queries[name]) for name in names if name in default_queries]

    if not selected_queries:
        print("No queries selected.")
        return None

    planned_total = len(selected_queries) * per_query_limit
    if planned_total > total_limit:
        raise ValueError(
            f"Selected {len(selected_queries)} queries with --per-query-limit {per_query_limit} "
            f"would fetch {planned_total} items, which exceeds --total-limit {total_limit}. "
            "Reduce --per-query-limit, reduce number of queries, or increase --total-limit (max 500)."
        )

    unique: dict[str, dict] = {}
    per_query_stats: list[dict] = []
    raw_fetched_total = 0

    for name, query in selected_queries:
        remaining_raw = total_limit - raw_fetched_total
        effective_limit = min(per_query_limit, remaining_raw)
        if effective_limit <= 0:
            break

        print(f'Running query "{name}" (limit {effective_limit}): {query}')

        try:
            raw_items = _call_apify_for_query(
                client,
                query=query,
                per_query_limit=effective_limit,
                max_total_charge_usd=max_total_charge_usd,
            )
        except Exception as e:
            print(f"Error calling Apify for query {name}: {e}")
            continue
        raw_fetched_total += len(raw_items)

        added = 0
        for item in raw_items:
            normalized = _normalize_tweet_item(item, source_query=name)
            tweet_id = normalized.get("id")
            if tweet_id is None:
                continue
            if tweet_id not in unique:
                unique[tweet_id] = normalized
                added += 1

        per_query_stats.append({"name": name, "fetched": len(raw_items), "added": added})

    results = list(unique.values())

    if output_file is None:
        output_file = os.path.join(base_dir, "viral_tweets.json")
    elif not os.path.isabs(output_file):
        output_file = os.path.join(base_dir, output_file)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} tweets to {output_file}.")
    for st in per_query_stats:
        print(f'- {st["name"]}: fetched={st["fetched"]} added={st["added"]}')

    return results

def scrape_viral_tweets(min_faves=300, days_back=2, max_tweets_to_fetch=50, apify_token: str | None = None):
    base_dir = _get_base_dir()
    resolved_token = _load_apify_token(base_dir, apify_token=apify_token)
    if not resolved_token:
        print("Error: APIFY_API_TOKEN is not set (env or twitter_agent/.env).")
        return None

    client = ApifyClient(resolved_token)
    
    # Load handles
    config_path = os.path.join(base_dir, "influencers.json")
    handles = get_influencers(config_path)
    
    if not handles:
        print("No handles found to scrape.")
        return None
        
    print(f"Loaded {len(handles)} influencers.")

    # Build the Advanced Search Query
    # Example format: (from:elonmusk OR from:VitalikButerin) min_faves:300 since:2026-02-27
    
    # Since Twitter limits query length, if we have 400+ handles we must split into chunks.
    # An advanced search query maxes out around 500 characters on Twitter.
    # We will safely chunk the handles into groups of 15 per query URL.
    
    chunk_size = 15
    handle_chunks = [handles[i:i + chunk_size] for i in range(0, len(handles), chunk_size)]
    
    start_urls = []
    
    # Calculate "since" date based on today
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    print(f"Building Advanced Search Queries (Since {since_date} | Min Faves: {min_faves})...")
    
    for chunk in handle_chunks:
        # e.g., "from:elonmusk OR from:Vitalik"
        from_string = " OR ".join([f"from:{h}" for h in chunk])
        
        # We URL encode the query piece by piece for safety
        search_query = f"({from_string}) min_faves:{min_faves} since:{since_date}"
        # For 'apidojo/tweet-scraper', search terms are commonly passed in `searchTerms` array
        start_urls.append(search_query)
        
    print(f"Generated {len(start_urls)} queries to execute.")

    # We use 'apidojo/tweet-scraper'
    run_input = {
        "searchTerms": start_urls,
        "searchMode": "live",
        "maxTweets": max_tweets_to_fetch
    }

    try:
        print(f"Starting Apify Actor ({ACTOR_ID})...")
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        
        print("Run finished! Fetching dataset results...")
        viral_tweets = []
        
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            viral_tweets.append(_normalize_tweet_item(item))
        
        # Ensure unique tweets (in case search overlaps) and sort by likes
        unique_tweets = {t["id"]: t for t in viral_tweets if t["id"] is not None}
        sorted_tweets = sorted(unique_tweets.values(), key=lambda x: x["likes"], reverse=True)
        
        # Save to file
        output_file = os.path.join(base_dir, "viral_tweets.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_tweets, f, indent=2, ensure_ascii=False)
            
        print(f"\\nSaved {len(sorted_tweets)} viral tweets to {output_file}.")
        
        return sorted_tweets
        
    except Exception as e:
        print(f"Error calling Apify: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Twitter Search Scraper via Apify")
    parser.add_argument("--mode", choices=["queries", "handles"], default="queries", help="Search mode to use")
    parser.add_argument("--apify-token", default=None, help="Apify token (overrides env/twitter_agent/.env)")
    parser.add_argument("--max-charge-usd", type=float, default=1.0, help="Per-run maximum Apify spend in USD")

    # queries mode args
    parser.add_argument("--topic", default="Polymarket", help="Search topic (queries mode)")
    parser.add_argument("--since-days", type=int, default=5, help="Days back for since:YYYY-MM-DD (queries mode)")
    parser.add_argument("--today-only", action="store_true", help="For the 'fresh' query use only today (since:today until:tomorrow)")
    parser.add_argument("--per-query-limit", type=int, default=100, help="Max tweets per query (<=100)")
    parser.add_argument("--total-limit", type=int, default=500, help="Max total tweets across all queries (<=500)")
    parser.add_argument("--include", nargs="*", default=None, help="Which default queries to run (popular viral fresh video gold)")
    parser.add_argument(
        "--query",
        action="append",
        default=None,
        help="Custom query (can be repeated). Supports {since},{today},{tomorrow},{yesterday},{fresh_since},{fresh_until}.",
    )
    parser.add_argument("--output", default=None, help="Output JSON path (relative to twitter_agent/ if not absolute)")

    # handles mode args (legacy)
    parser.add_argument("--min_likes", type=int, default=300, help="Minimum likes to be considered viral")
    parser.add_argument("--days", type=int, default=2, help="How many days back to search")
    parser.add_argument("--limit", type=int, default=100, help="Global max tweets to return")
    
    args = parser.parse_args()
    if args.mode == "handles":
        scrape_viral_tweets(
            min_faves=args.min_likes,
            days_back=args.days,
            max_tweets_to_fetch=args.limit,
            apify_token=args.apify_token,
        )
    else:
        scrape_operator_queries(
            topic=args.topic,
            since_days=args.since_days,
            per_query_limit=args.per_query_limit,
            total_limit=args.total_limit,
            include=args.include,
            queries=args.query,
            today_only=args.today_only,
            apify_token=args.apify_token,
            max_total_charge_usd=args.max_charge_usd,
            output_file=args.output,
        )
