import os
import requests
import json
from datetime import datetime

# Config
SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def get_free_games():
    """Get current and upcoming free games with simple error handling"""
    try:
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        params = {"locale": "zh-CN", "country": "CN"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        elements = data['data']['Catalog']['searchStore']['elements']
        
        current_free = []
        upcoming_free = []
        
        for game in elements:
            promotions = game.get('promotions', {})
            offers = promotions.get('promotionalOffers', [])
            
            if offers:
                # Current free games
                if any(offer['discountSetting']['discountPercentage'] == 0 
                       for promo in offers 
                       for offer in promo['promotionalOffers']):
                    current_free.append({
                        'title': game['title'],
                        'url': f"https://www.epicgames.com/store/p/{game['productSlug']}"
                    })
                # Upcoming games
                else:
                    upcoming_free.append({
                        'title': game['title'],
                        'start_date': offers[0]['promotionalOffers'][0]['startDate'][:10]  # YYYY-MM-DD
                    })
        
        return current_free, upcoming_free
        
    except Exception as e:
        print(f"API Error: {e}")
        return [], []  # Return empty lists on failure

def send_notification(current, upcoming):
    """Send clean Server酱 message"""
    message = "🎮 **Currently Free:**\n"
    message += "\n".join(f"- [{game['title']}]({game['url']})" for game in current)
    
    if upcoming:
        message += "\n\n⏳ **Coming Soon:**\n"
        message += "\n".join(f"- {game['title']} (Free on {game['start_date']})" for game in upcoming)
    
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic Free Games", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    # Load cache
    try:
        with open(CACHE_FILE) as f:
            cached_games = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached_games = []
    
    # Check games
    current, upcoming = get_free_games()
    new_games = [g for g in current if g not in cached_games]
    
    # Notify if new games found
    if new_games:
        send_notification(current, upcoming)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current, f)