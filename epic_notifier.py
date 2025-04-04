import os
import requests
import json
from datetime import datetime

# Configuration
SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"
ERROR_FILE = "api_error.log"

def detect_api_structure(response):
    """Try multiple response format patterns"""
    data = response.json()
    
    # Pattern 1 (Current)
    if 'data' in data and 'Catalog' in data['data']:
        return data['data']['Catalog']['searchStore']['elements']
    
    # Pattern 2 (Alternative observed in past)
    if 'elements' in data:
        return data['elements']
    
    # Pattern 3 (Fallback)
    return data.get('games', [])

def get_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    params = {"locale": "zh-CN", "country": "CN"}
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        
        games = detect_api_structure(response)
        if not games:
            log_error("API returned empty data", response.text)
            return [], []
            
        current_free = []
        for game in games:
            try:
                if is_currently_free(game):
                    current_free.append({
                        'title': game.get('title', 'Unknown'),
                        'productSlug': game.get('productSlug', ''),
                        'startDate': find_deep(game, ['promotions', 'promotionalOffers', 0, 'promotionalOffers', 0, 'startDate'])
                    })
            except Exception as e:
                log_error(f"Game parsing failed: {str(e)}", game)
        
        return current_free, []
        
    except Exception as e:
        log_error(f"API request failed: {str(e)}")
        return [], []

def is_currently_free(game):
    """Multi-layered check for free status"""
    discount = find_deep(game, ['promotions', 'promotionalOffers', 0, 'promotionalOffers', 0, 'discountSetting', 'discountPercentage'])
    return discount == 0

def find_deep(obj, keys):
    """Safely navigate nested structures"""
    for key in keys:
        try:
            obj = obj[key]
        except (TypeError, KeyError, IndexError):
            return None
    return obj

def log_error(message, details=""):
    """Record API issues with timestamp"""
    with open(ERROR_FILE, 'a') as f:
        f.write(f"{datetime.now()} - {message}\n")
        if details:
            f.write(f"Details: {str(details)[:500]}...\n\n")

# ... (rest of the script remains the same)

def send_notification(current, upcoming):
    if not current and not upcoming:
        return
        
    message = "🎮 **Currently Free:**\n" + "\n".join(
        f"- {game['title']}: https://www.epicgames.com/store/p/{game['productSlug']}"
        for game in current
    )
    
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic Free Games", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    current, upcoming = get_free_games()
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cached = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached = []
    
    new_games = [g for g in current if g not in cached]
    
    if new_games:
        send_notification(new_games, upcoming)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current, f)