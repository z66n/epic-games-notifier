import os
import requests
import json

SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def get_free_games():
    try:
        response = requests.get(
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
            params={"locale": "zh-CN", "country": "CN"},
            timeout=10
        )
        data = response.json()
        
        # Fail fast if API structure changed
        if not data or not data.get('data', {}).get('Catalog', {}).get('searchStore'):
            return [], []
            
        games = data['data']['Catalog']['searchStore']['elements']
        current = []
        upcoming = []
        
        for game in games:
            title = game.get('title', 'Unknown Game')
            promotions = game.get('promotions', {})
            
            if not promotions:
                continue
                
            # Current free games
            if any(offer['discountSetting']['discountPercentage'] == 0 
                   for promo in promotions.get('promotionalOffers', [])
                   for offer in promo.get('promotionalOffers', [])):
                current.append({
                    'title': title,
                    'url': f"https://epicgames.com/store/p/{game.get('productSlug', '')}"
                })
            # Upcoming games
            elif promotions.get('promotionalOffers'):
                upcoming.append({
                    'title': title,
                    'date': promotions['promotionalOffers'][0]['promotionalOffers'][0]['startDate'][:10]  # YYYY-MM-DD
                })
                
        return current, upcoming
        
    except Exception:
        return [], []  # Return empty lists on any error

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