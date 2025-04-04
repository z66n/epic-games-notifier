import os
import requests
import json
from datetime import datetime, timezone

# Configuration
SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def get_free_games():
    """Fetch current free games with robust error handling"""
    try:
        response = requests.get(
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
            params={"locale": "zh-CN", "country": "CN"},
            timeout=15
        )
        data = response.json()
        
        # Safely extract game elements
        elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
        
        current, upcoming = [], []
        now = datetime.now(timezone.utc)
        
        for game in elements:
            title = game.get('title', 'Unknown Game')
            promotions = game.get('promotions', {})
            
            # Check current free games
            for promo in promotions.get('promotionalOffers', []):
                for offer in promo.get('promotionalOffers', []):
                    if offer.get('discountSetting', {}).get('discountPercentage') == 0:
                        start = datetime.fromisoformat(offer['startDate'].replace('Z', '+00:00'))
                        end = datetime.fromisoformat(offer['endDate'].replace('Z', '+00:00'))
                        
                        if start <= now < end:  # Currently free
                            current.append({
                                'title': title,
                                'url': f"https://epicgames.com/store/p/{game.get('productSlug', '')}",
                                'end_date': end.strftime('%Y-%m-%d')
                            })
                        elif now < start:  # Upcoming
                            upcoming.append({
                                'title': title,
                                'start_date': start.strftime('%Y-%m-%d')
                            })
        
        return current, upcoming
        
    except Exception as e:
        print(f"API Error: {e}")
        return [], []  # Return empty lists on failure

def send_notification(current, upcoming):
    """Send formatted message via Server酱"""
    message = "🎮 **Currently Free:**\n" + "\n".join(
        f"- [{game['title']}]({game['url']}) (Until {game['end_date']})"
        for game in current
    )
    
    if upcoming:
        message += "\n\n⏳ **Coming Soon:**\n" + "\n".join(
            f"- {game['title']} (Free from {game['start_date']})"
            for game in upcoming
        )
    
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic Free Games Update", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    # Load cache
    try:
        with open(CACHE_FILE) as f:
            cached = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached = []
    
    # Check for new games
    current, upcoming = get_free_games()
    new_games = [g for g in current if g not in cached]
    
    # Send notification if new games found
    if new_games or (not cached and current):
        send_notification(current, upcoming)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current, f)