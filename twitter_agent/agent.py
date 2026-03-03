import argparse
import importlib.util
import json
import os
import sys

from dotenv import load_dotenv


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _load_env() -> None:
    load_dotenv(os.path.join(_base_dir(), ".env"))


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _truncate(text: str, n: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def _summarize_apify_items(items: list[dict], *, top_n: int = 30) -> dict:
    def likes_of(item: dict) -> int:
        return int(item.get("likes") or 0)

    sorted_items = sorted(items, key=likes_of, reverse=True)
    top = []
    for it in sorted_items[:top_n]:
        top.append(
            {
                "id": it.get("id"),
                "author": it.get("author"),
                "likes": it.get("likes"),
                "retweets": it.get("retweets"),
                "created_at": it.get("created_at"),
                "url": it.get("url"),
                "source_query": it.get("source_query"),
                "text": _truncate(it.get("text", ""), 220),
            }
        )
    return {
        "count": len(items),
        "top": top,
    }


def _tool_apify_x_search(args: dict) -> dict:
    scrape_path = os.path.join(_base_dir(), "tools", "scrape_profiles.py")
    mod = _load_module("scrape_profiles", scrape_path)

    topic = args.get("topic", "Polymarket")
    since_days = int(args.get("since_days", 5))
    per_query_limit = int(args.get("per_query_limit", 100))
    total_limit = int(args.get("total_limit", 500))
    today_only = bool(args.get("today_only", False))
    include = args.get("include")
    queries = args.get("queries")
    max_charge_usd = args.get("max_charge_usd", 1.0)

    results = mod.scrape_operator_queries(
        topic=topic,
        since_days=since_days,
        per_query_limit=per_query_limit,
        total_limit=total_limit,
        include=include,
        queries=queries,
        today_only=today_only,
        apify_token=args.get("apify_token"),
        max_total_charge_usd=max_charge_usd,
        output_file=args.get("output_file"),
    )
    if results is None:
        return {"ok": False, "error": "apify returned no results"}

    return {"ok": True, "summary": _summarize_apify_items(results)}


def _tool_tavily_search(args: dict) -> dict:
    tavily_path = os.path.join(_base_dir(), "tools", "search_tavily.py")
    mod = _load_module("search_tavily", tavily_path)

    query = args["query"]
    depth = args.get("depth", "advanced")
    max_results = int(args.get("max_results", 5))

    results = mod.search_tavily(query, search_depth=depth, max_results=max_results)
    if results is None:
        return {"ok": False, "error": "tavily returned no results"}
    return {"ok": True, "results": results}


def _tool_brave_search(args: dict) -> dict:
    brave_path = os.path.join(_base_dir(), "tools", "search_brave.py")
    mod = _load_module("search_brave", brave_path)

    query = args["query"]
    count = int(args.get("count", 5))

    results = mod.search_brave(query, count=count)
    if results is None:
        return {"ok": False, "error": "brave returned no results"}
    return {"ok": True, "results": results}


TOOLS = {
    "apify_x_search": _tool_apify_x_search,
    "tavily_search": _tool_tavily_search,
    "brave_search": _tool_brave_search,
}


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser(
        description="twitter_agent tool runner (no LLM calls). Use to collect receipts for the main Codex agent."
    )
    sub = parser.add_subparsers(dest="tool", required=True)

    apify = sub.add_parser("apify_x_search", help="Search X/Twitter via Apify and print a summarized receipt JSON")
    apify.add_argument("--topic", default="Polymarket")
    apify.add_argument("--since-days", type=int, default=5)
    apify.add_argument("--per-query-limit", type=int, default=100)
    apify.add_argument("--total-limit", type=int, default=500)
    apify.add_argument("--today-only", action="store_true")
    apify.add_argument(
        "--include",
        nargs="*",
        default=None,
        help='Which default query buckets to include (e.g. "popular viral fresh video gold"). If omitted, uses all.',
    )
    apify.add_argument(
        "--query",
        dest="queries",
        action="append",
        default=None,
        help="Custom query template (repeatable). Supports {today},{tomorrow},{since},{fresh_since},{fresh_until}.",
    )
    apify.add_argument("--apify-token", default=None)
    apify.add_argument("--max-charge-usd", type=float, default=1.0)
    apify.add_argument("--output-file", default=None)

    tavily = sub.add_parser("tavily_search", help="Web research via Tavily and print results JSON")
    tavily.add_argument("query")
    tavily.add_argument("--depth", default="advanced")
    tavily.add_argument("--max-results", type=int, default=5)

    brave = sub.add_parser("brave_search", help="Web research via Brave and print results JSON")
    brave.add_argument("query")
    brave.add_argument("--count", type=int, default=5)

    args = parser.parse_args()
    tool_name = args.tool
    if tool_name not in TOOLS:
        print(f"Unknown tool {tool_name}. Allowed: {', '.join(sorted(TOOLS.keys()))}.", file=sys.stderr)
        return 2

    tool_args = vars(args).copy()
    tool_args.pop("tool", None)

    try:
        result = TOOLS[tool_name](tool_args)
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    _print_json(result)
    return 0 if bool(result.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
