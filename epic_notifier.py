import os
import requests
import json
from datetime import datetime, timezone

SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def safe_get(data, keys, default=None):
    """Safely navigate nested dictionaries/lists"""
    for key in keys:
        try:
            data = data[key]
        except (TypeError, KeyError, IndexError, AttributeError):
            return default
    return data

def get_free_games():
    try:
        response = requests.get(
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
            params={"locale": "zh-CN", "country": "CN"},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()
        
        # Safely extract elements with multiple fallbacks
        elements = safe_get(data, ['data', 'Catalog', 'searchStore', 'elements'], [])
        if not elements:
            elements = safe_get(data, ['elements'], [])
        
        current, upcoming = [], []
        now = datetime.now(timezone.utc)
        
        for game in elements:
            try:
                title = safe_get(game, ['title'], 'Unknown Game')
                promotions = safe_get(game, ['promotions'], {})
                
                # Current free games
                for promo in safe_get(promotions, ['promotionalOffers'], []):
                    for offer in safe_get(promo, ['promotionalOffers'], []):
                        if safe_get(offer, ['discountSetting', 'discountPercentage']) == 0:
                            start_str = safe_get(offer, ['startDate'])
                            end_str = safe_get(offer, ['endDate'])
                            
                            if start_str and end_str:
                                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                                end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                                
                                if start <= now < end:
                                    current.append({
                                        'title': title,
                                        'url': f"https://epicgames.com/store/p/{safe_get(game, ['productSlug'], '')}",
                                        'end_date': end.strftime('%Y-%m-%d')
                                    })
                
                # Upcoming games
                for promo in safe_get(promotions, ['upcomingPromotionalOffers'], []):
                    for offer in safe_get(promo, ['promotionalOffers'], []):
                        if safe_get(offer, ['discountSetting', 'discountPercentage']) == 0:
                            start_str = safe_get(offer, ['startDate'])
                            if start_str:
                                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                                upcoming.append({
                                    'title': title,
                                    'start_date': start.strftime('%Y-%m-%d'),
                                    'url': f"https://epicgames.com/store/p/{safe_get(game, ['productSlug'], '')}"
                                })
            
            except Exception as e:
                print(f"Skipping game due to error: {e}")
                continue
                
        return current, upcoming
        
    except Exception as e:
        print(f"API Error: {e}")
        return [], []

def send_notification(new_games, upcoming):
    if not new_games and not upcoming:
        return
        
    message = "🎮 **New Free Games:**\n" + "\n".join(
        f"- [{game['title']}]({game['url']}) (Until {game['end_date']})"
        for game in new_games
    ) if new_games else "🎮 No new free games this week\n"
    
    if upcoming:
        message += "\n\n⏳ **Upcoming Games:**\n" + "\n".join(
            f"- [{game['title']}]({game['url']}) (Free from {game['start_date']})"
            for game in upcoming
        )
    
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
            data={"title": "Epic Games Update", "desp": message},
            timeout=10
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")

if __name__ == "__main__":
    # Initialize cache if missing
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'w') as f:
            json.dump([], f)
    
    # Load cache
    try:
        with open(CACHE_FILE) as f:
            cached = json.load(f)
    except Exception as e:
        print(f"Cache error: {e}")
        cached = []
    
    current, upcoming = get_free_games()
    new_games = [g for g in current if g not in cached]
    
    # Notification logic
    if new_games or not cached:
        send_notification(new_games if new_games else current, upcoming)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current, f)
    else:
        print("No new games - skipping notification")