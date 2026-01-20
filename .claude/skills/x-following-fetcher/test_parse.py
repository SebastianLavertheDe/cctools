import json
import subprocess
import shlex
from pathlib import Path

X_CURL_FILE = Path('/home/say/cctools/.claude/skills/x-following-fetcher/x_curl.txt')
OUTPUT_DIR = Path('/home/say/cctools/x')

def execute_curl_from_file():
    with open(X_CURL_FILE, 'r') as f:
        curl_content = f.read().strip()
    curl_cmd = curl_content.replace('\\\n', ' ').replace('\\\r\n', ' ')
    cmd_list = shlex.split(curl_cmd)
    return subprocess.run(cmd_list, capture_output=True, text=True, timeout=30)

def parse_tweet_entry(entry):
    try:
        content = entry.get('content', {})
        tweet = content.get('itemContent', {})

        if tweet.get('__typename') != 'TweetTombstone':
            tweet_results = tweet.get('tweet_results', {})
            if tweet_results:
                result = tweet_results.get('result', {})
                legacy = result.get('legacy', {})
                
                user = {}
                user_core = {}
                core = result.get('core', {})
                user_results = core.get('user_results', {}).get('result', {})
                
                if user_results:
                    user_core = user_results.get('core', {})
                    if user_core:
                        user = user_core
                
                if not user.get('screen_name'):
                    user_legacy = user_results.get('legacy', {})
                    if user_legacy:
                        user = user_legacy
                
                user_name = user.get('name', '')
                user_screen_name = user.get('screen_name', '')
                
                return {
                    'id': legacy.get('id_str', ''),
                    'user_name': user_name,
                    'user_screen_name': user_screen_name,
                    'content': legacy.get('full_text', ''),
                    'created_at': legacy.get('created_at', ''),
                }
        return None
    except Exception as e:
        print(f'Parse error: {e}')
        return None

if __name__ == '__main__':
    result = execute_curl_from_file()
    if result.returncode == 0:
        data = json.loads(result.stdout)
        instructions = data.get('data', {}).get('home', {}).get('home_timeline_urt', {}).get('instructions', [])
        tweets = []
        for instr in instructions:
            if instr.get('type') == 'TimelineAddEntries':
                for entry in instr.get('entries', []):
                    tweet = parse_tweet_entry(entry)
                    if tweet:
                        tweets.append(tweet)
        
        print(f'Parsed {len(tweets)} tweets')
        for t in tweets[:3]:
            print(f"@{t['user_screen_name']}: {t['content'][:50]}...")
