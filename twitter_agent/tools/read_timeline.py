import os
import json
import argparse
from dotenv import load_dotenv
import tweepy

def read_timeline(max_results=10):
    load_dotenv()
    
    # Needs Twitter API v2 credentials
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Error: Missing Twitter API credentials in .env")
        return None
        
    try:
        # Initialize client
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Get authenticated user ID
        me = client.get_me()
        user_id = me.data.id
        
        # We use get_home_timeline, which requires OAuth 1.0a User Context (which access_token provides)
        response = client.get_home_timeline(max_results=max_results, tweet_fields=["created_at", "author_id", "public_metrics"], expansions=["author_id"])
        
        if not response.data:
            print("No tweets found or timeline is empty.")
            return []
            
        # Create a dictionary of users for easy mapping
        users = {u["id"]: u for u in response.includes.get("users", [])}
        
        tweets = []
        for tweet in response.data:
            author = users.get(tweet.author_id)
            username = author.username if author else "Unknown"
            
            tweets.append({
                "id": tweet.id,
                "author": username,
                "text": tweet.text,
                "created_at": str(tweet.created_at),
                "metrics": tweet.public_metrics
            })
            
        print(json.dumps(tweets, indent=2, ensure_ascii=False))
        return tweets
        
    except Exception as e:
        print(f"Error reading timeline: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Timeline Reader")
    parser.add_argument("--count", type=int, default=10, help="Number of tweets to fetch (max 100)")
    
    args = parser.parse_args()
    read_timeline(args.count)
