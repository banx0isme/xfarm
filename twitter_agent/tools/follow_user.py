import os
import argparse
from dotenv import load_dotenv
import tweepy

def follow_user(target_handle):
    load_dotenv()
    
    # Needs Twitter API v2 credentials with Read/Write Access
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Error: Missing Twitter API credentials in .env")
        return False
        
    try:
        # Initialize client
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # 1. Get our own user_id
        me = client.get_me()
        my_id = me.data.id
        print(f"Authenticated as User ID: {my_id}")
        
        # 2. Prevent the "@" symbol from breaking the lookup
        target_handle = target_handle.lstrip("@")
        
        # 3. Lookup the target user by username (handle)
        target_user = client.get_user(username=target_handle)
        if not target_user.data:
            print(f"Error: Could not find user '{target_handle}'")
            return False
            
        target_id = target_user.data.id
        print(f"Found target user: @{target_user.data.username} (ID: {target_id})")
        
        # 4. Execute the follow action
        response = client.follow_user(target_user_id=target_id)
        
        if response.data.get("following"):
            print(f"Success! You are now following @{target_user.data.username}")
            return True
        elif response.data.get("pending_follow"):
            print(f"Follow request sent to @{target_user.data.username} (Account is private)")
            return True
        else:
            print(f"Failed or already following @{target_user.data.username}")
            return False
            
    except tweepy.errors.TooManyRequests as e:
        print(f"Rate limit exceeded: {e}")
        return False
    except tweepy.errors.Forbidden as e:
        print(f"Permission denied (Check App permissions in Dev Portal): {e}")
        return False
    except Exception as e:
        print(f"Error following user: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Follow User Tool")
    parser.add_argument("handle", type=str, help="Twitter handle to follow (e.g. elonmusk or @elonmusk)")
    
    args = parser.parse_args()
    follow_user(args.handle)
