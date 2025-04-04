import os
import requests
import json
from datetime import datetime, timezone

SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def is_currently_free(promotions):
    """Check if game is free right now"""
    for promo in promotions.get('promotionalOffers', []):
        for offer in promo.get('promotionalOffers', []):
            if (offer.get('discountSetting', {}).get('discountPercentage') == 0 and
                datetime.now(timezone.utc) < datetime.fromisoformat(offer['endDate'])):
                return True
    return False

def is_upcoming(promotions):
    """Check if game is upcoming (not yet free)"""
    now = datetime.now(timezone.utc)
    for promo in promotions.get('promotionalOffers', []):
        for offer in promo.get('promotionalOffers', []):
            start = datetime.fromisoformat(offer['startDate'])
            end = datetime.fromisoformat(offer['endDate'])
            if start > now and offer.get('discountSetting', {}).get('discountPercentage') == 0:
                return True
    return False

def get_free_games():
    try:
        response = requests.get(
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
            params={"locale": "zh-CN", "country": "CN"},
            timeout=10
        )
        data = response.json()
        games = data['data']['Catalog']['searchStore']['elements']
        
        current = []
        upcoming = []
        
        for game in games:
            promotions = game.get('promotions', {})
            if not promotions:
                continue
                
            if is_currently_free(promotions):
                current.append({
                    'title': game.get('title', 'Unknown Game'),
                    'url': f"https://epicgames.com/store/p/{game.get('productSlug', '')}"
                })
            elif is_upcoming(promotions):
                upcoming.append({
                    'title': game.get('title', 'Unknown Game'),
                    'date': next(
                        offer['startDate'][:10] 
                        for promo in promotions['promotionalOffers'] 
                        for offer in promo['promotionalOffers'] 
                        if datetime.fromisoformat(offer['startDate']) > datetime.now(timezone.utc)
                    )
                })
                
        return current, upcoming
        
    except Exception:
        return [], []

def send_notification(current, upcoming):
    message = "🎮 **Currently Free:**\n" + "\n".join(
        f"- [{game['title']}]({game['url']})" for game in current
    )
    if upcoming:
        message += "\n\n⏳ **Coming Soon:**\n" + "\n".join(
            f"- {game['title']} (Free on {game['date']})" for game in upcoming
        )
    
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic Free Games", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    current, upcoming = get_free_games()
    
    # Load cache
    try:
        with open(CACHE_FILE) as f:
            cached = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached = []
    
    # Find new games
    new_games = [g for g in current if g not in cached]
    
    if new_games:
        send_notification(current, upcoming)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current, f)