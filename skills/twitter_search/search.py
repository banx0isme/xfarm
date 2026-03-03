import argparse
import json
import logging
import os
import sys
from apify_client import ApifyClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def _get_apify_token() -> str | None:
    return os.getenv("APIFY_API_TOKEN")

def main():
    parser = argparse.ArgumentParser(description="Search Twitter using Apify apidojo/tweet-scraper.")
    parser.add_argument("searchTerms", nargs="+", help="Terms to search for.")
    parser.add_argument("--max-items", type=int, default=100, help="Maximum number of items to scrape.")
    parser.add_argument("--output", default="tweets_results.json", help="Output JSON file name.")
    args = parser.parse_args()

    # Initialize the ApifyClient
    logging.info("Initializing ApifyClient...")
    token = _get_apify_token()
    if not token:
        logging.error("APIFY_API_TOKEN is not set in environment.")
        sys.exit(1)
    client = ApifyClient(token)

    # Prepare the Actor input
    run_input = {
        "searchTerms": args.searchTerms,
        "maxItems": args.max_items,
        "sort": "Latest"
    }

    logging.info(f"Running apidojo/tweet-scraper for terms: {args.searchTerms} (max_items={args.max_items})")
    
    # Run the Actor and strictly limit the spend to $1.0
    try:
        run = client.actor("apidojo/tweet-scraper").call(
            run_input=run_input,
            max_total_charge_usd=1.0  # Limits the run cost to exactly $1 USD maximum
        )
    except Exception as e:
        logging.error(f"Failed to call Apify API: {e}")
        sys.exit(1)

    if not run:
        logging.error("Failed to start run.")
        sys.exit(1)
        
    logging.info(f"Run completed. Dataset ID: {run.get('defaultDatasetId')}")

    # Fetch and save Actor results from the run's dataset
    logging.info("Fetching results...")
    dataset_client = client.dataset(run["defaultDatasetId"])
    items = dataset_client.list_items().items

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
        logging.info(f"Saved {len(items)} tweets to {args.output}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")

if __name__ == "__main__":
    main()
