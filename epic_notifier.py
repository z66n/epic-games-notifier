import os
import requests
import json  # ADD THIS IMPORT
from datetime import datetime

SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def is_currently_free(game):
    """Check if a game is currently free (not upcoming)"""
    promotions = game.get('promotions', {}).get('promotionalOffers', [])
    return any(
        offer['discountSetting']['discountPercentage'] == 0
        for promo in promotions
        for offer in promo['promotionalOffers']
    )

def get_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    params = {"locale": "zh-CN", "country": "CN"}
    try:
        response = requests.get(url, params=params, timeout=10)
        all_games = response.json()['data']['Catalog']['searchStore']['elements']
        
        # Separate current and upcoming
        current_free = [g for g in all_games if is_currently_free(g)]
        upcoming_free = [g for g in all_games 
                       if g.get('promotions') 
                       and not is_currently_free(g)]
        
        return current_free, upcoming_free
    except Exception as e:
        print(f"Error fetching games: {e}")
        return [], []

def send_notification(current, upcoming):
    message = "🎮 **Currently Free:**\n"
    message += "\n".join(
        f"- {game['title']}: <https://www.epicgames.com/store/p/{game.get('productSlug', '')}>"
        for game in current
    )
    
    if upcoming:
        message += "\n\n⏳ **Coming Soon:**\n"
        message += "\n".join(
            f"- {game['title']} (Free from {game['promotions']['promotionalOffers'][0]['promotionalOffers'][0]['startDate']})"
            for game in upcoming
        )
    
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic Games Update", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    current_free, upcoming_free = get_free_games()
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cached_games = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached_games = []
    
    # Only compare current free games with cache
    new_free_games = [
        g for g in current_free
        if g['title'] not in [c['title'] for c in cached_games]
    ]
    
    if new_free_games or (current_free and not cached_games):
        send_notification(current_free, upcoming_free)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current_free, f)  # Only cache CURRENTLY free games