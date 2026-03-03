---
name: Twitter Search using Apify
description: A skill to search Twitter using the apidojo/tweet-scraper actor on Apify.
---

# Twitter Search SKILL

This skill allows you to search for tweets on Twitter using the Apify API (`apidojo/tweet-scraper` actor) while enforcing a strict daily maximum spend limit of $1 per run.

## Prerequisites

- Python 3
- `apify-client` package installed
  ```bash
  pip install apify-client
  ```

## Usage

Use the provided `search.py` script to perform a Twitter search.
The script automatically sets `max_total_charge_usd=1.0` so that your runs will not exceed $1.

Run the script by providing search terms as arguments:

```bash
python3 /Users/pavel/ai_agent_farm/skills/twitter_search/search.py "Ethereum" "Polymarket"
```

The script will output the retrieved tweets in JSON format to `tweets_results.json` and print a summary.

### Parameters
You can edit `search.py` to change `searchTerms` and `maxItems`. By default, it searches for the query terms you supply in arguments, with `maxItems` set to 100.

## API Key Setup
Set the `APIFY_API_TOKEN` environment variable before running:

```bash
export APIFY_API_TOKEN="apify_api_..."
```

For the more advanced “operator queries” workflow (batch queries, per-query limits, total cap, etc.), see:

- `/Users/pavel/ai_agent_farm/twitter_agent/SEARCH_APIFY.md`
