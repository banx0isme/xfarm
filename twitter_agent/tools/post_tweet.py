import os
import argparse
from dotenv import load_dotenv
import tweepy

def post_tweet(text):
    load_dotenv()
    
    # Needs Twitter API v2 credentials
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Error: Missing Twitter API credentials in .env")
        return False
        
    try:
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        response = client.create_tweet(text=text)
        print(f"Successfully posted tweet! ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Publishing Tool")
    parser.add_argument("text", type=str, help="Text to tweet")
    
    args = parser.parse_args()
    post_tweet(args.text)
