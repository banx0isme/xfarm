# Apify Search (X/Twitter) — Current Workflow

This repository uses **Apify** to search/scrape posts from X (Twitter) via the Apify Actor:

- `apidojo/tweet-scraper`

The main entrypoint is:

- `/Users/pavel/ai_agent_farm/twitter_agent/tools/scrape_profiles.py`

## Prerequisites

Set an Apify token (preferred: in `twitter_agent/.env`, or export it in your shell):

```bash
export APIFY_API_TOKEN="apify_api_..."
```

`scrape_profiles.py` also supports passing the token explicitly:

```bash
python3 /Users/pavel/ai_agent_farm/twitter_agent/tools/scrape_profiles.py --apify-token "apify_api_..." ...
```

## Default search mode (recommended): operator queries

By default, the script runs in `--mode queries` and executes a **bundle of “X operator queries”** for a topic.

### Defaults

- `--mode queries`
- `--topic "Polymarket"`
- `--since-days 5` (used for `since:YYYY-MM-DD`)
- `--per-query-limit 100` (hard cap: must be `<= 100`)
- `--total-limit 500` (hard cap: must be `<= 500`)
- `--max-charge-usd 1.0` (Apify per-run spend cap, applied per query-run)
- Output: `twitter_agent/viral_tweets.json`

### Built-in query bundle

The default bundle contains 5 queries (names in parentheses). The script prints each query before it runs.

- Popular posts (popular):
  - `{topic} min_retweets:30 filter:media since:{since}`
- Very viral posts (viral):
  - `{topic} min_retweets:100 min_faves:200 filter:media since:{since}`
- Fresh / trending (fresh):
  - `{topic} min_retweets:20 filter:media since:{fresh_since}`
  - If `--today-only` is provided:
    - `{topic} min_retweets:20 filter:media since:{today} until:{tomorrow}`
- Video posts (video):
  - `{topic} filter:videos min_faves:50 since:{since}`
- “Gold formula” (gold):
  - `{topic} min_retweets:30 min_faves:50 filter:media -filter:retweets since:{since}`

### Output shape

The script normalizes raw Apify items into:

- `id`, `author`, `text`, `likes`, `retweets`, `created_at`, `url`
- `source_query` — which query name produced the tweet (e.g. `gold`, `viral`, …)

Tweets are **deduplicated by `id` across all queries**. This means you may end up with fewer than 500 unique tweets if the same posts appear in multiple queries.

### “Full coverage” run (5×100 = 500)

This runs all 5 built-in queries with 100 results each, for a total of 500 fetched items:

```bash
APIFY_API_TOKEN="apify_api_..." python3 /Users/pavel/ai_agent_farm/twitter_agent/tools/scrape_profiles.py \
  --mode queries \
  --topic "Polymarket" \
  --per-query-limit 100 \
  --total-limit 500
```

### Run only some queries

```bash
python3 /Users/pavel/ai_agent_farm/twitter_agent/tools/scrape_profiles.py \
  --mode queries \
  --include gold viral popular \
  --per-query-limit 100 \
  --total-limit 300
```

The script enforces: `len(selected_queries) * per_query_limit <= total_limit`.

### Custom queries

You can provide one or more `--query` arguments. Each query supports placeholders:

- `{since}`, `{today}`, `{tomorrow}`, `{yesterday}`, `{fresh_since}`, `{fresh_until}`

Example:

```bash
python3 /Users/pavel/ai_agent_farm/twitter_agent/tools/scrape_profiles.py \
  --mode queries \
  --query 'Polymarket min_retweets:30 filter:media -filter:retweets since:{since}' \
  --query 'Polymarket filter:videos min_faves:50 since:{since}' \
  --per-query-limit 100 \
  --total-limit 200
```

## Legacy mode: handles list

The old approach (`--mode handles`) builds advanced queries from `twitter_agent/influencers.json` and runs the same Apify Actor.

This is kept for backward compatibility, but the operator-query mode is the recommended default.

