import os
import requests
from datetime import datetime

SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY")
CACHE_FILE = "games_cache.json"

def get_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    params = {"locale": "zh-CN", "country": "CN"}
    try:
        response = requests.get(url, params=params, timeout=10)
        return [game for game in response.json()['data']['Catalog']['searchStore']['elements'] 
                if game.get('promotions')]
    except Exception as e:
        print(f"Error fetching games: {e}")
        return None

def send_notification(games):
    message = "\n".join(
        f"🎮 {game['title']}\n"
        f"🔗 https://www.epicgames.com/store/p/{game.get('productSlug', '')}\n"
        for game in games
    )
    requests.post(
        f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
        data={"title": "Epic新免费游戏!", "desp": message},
        timeout=10
    )

if __name__ == "__main__":
    current_games = get_free_games()
    if not current_games:
        exit()
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cached_games = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached_games = []
    
    new_games = [
        game for game in current_games 
        if game['title'] not in [g['title'] for g in cached_games]
    ]
    
    if new_games:
        send_notification(new_games)
        with open(CACHE_FILE, 'w') as f:
            json.dump(current_games, f)