import os
import requests
import json
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SERVER_CHAN_KEY = "SCT1a2b3c4d5e6f7g8h9i0j"  # 替换为你的Server酱Key
CACHE_FILE = "games_cache.json"
TIME_ZONE = "UTC" # 替换为你的时区，例如 "Asia/Shanghai" 或 "America/New_York"


def safe_get(data, keys, default=None):
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
            params={"locale": "zh-CN", "country": "CA"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        # Safely extract elements with multiple fallbacks
        elements = safe_get(data, ["data", "Catalog", "searchStore", "elements"], [])
        if not elements:
            elements = safe_get(data, ["elements"], [])

        current, upcoming = [], []
        earliest_upcoming = None
        now = datetime.now(timezone.utc)

        for game in elements:
            try:
                title = safe_get(game, ["title"], "Unknown Game")
                promotions = safe_get(game, ["promotions"], {})
                slug = (
                    safe_get(game, ["offerMappings", 0, "pageSlug"], "")
                    or safe_get(game, ["catalogNs", "mappings", 0, "pageSlug"], "")
                    or safe_get(game, ["productSlug"], "")
                    or "not-found"
                )

                # Current free games
                for promo in safe_get(promotions, ["promotionalOffers"], []):
                    for offer in safe_get(promo, ["promotionalOffers"], []):
                        if (
                            safe_get(offer, ["discountSetting", "discountPercentage"])
                            == 0
                        ):
                            start_str = safe_get(offer, ["startDate"])
                            end_str = safe_get(offer, ["endDate"])

                            if start_str and end_str:
                                start = datetime.fromisoformat(
                                    start_str.replace("Z", "+00:00")
                                )
                                end = datetime.fromisoformat(
                                    end_str.replace("Z", "+00:00")
                                )

                                if start <= now < end:
                                    current.append(
                                        {
                                            "title": title,
                                            "url": f"https://store.epicgames.com/p/{slug}",
                                            "end_date": end.strftime("%Y-%m-%d"),
                                        }
                                    )

                # Upcoming games
                for promo in safe_get(promotions, ["upcomingPromotionalOffers"], []):
                    for offer in safe_get(promo, ["promotionalOffers"], []):
                        if (
                            safe_get(offer, ["discountSetting", "discountPercentage"])
                            == 0
                        ):
                            start_str = safe_get(offer, ["startDate"])
                            if start_str:
                                start = datetime.fromisoformat(
                                    start_str.replace("Z", "+00:00")
                                )
                                upcoming.append(
                                    {
                                        "title": title,
                                        "start_date": start.strftime("%Y-%m-%d"),
                                        "url": f"https://store.epicgames.com/p/{slug}",
                                    }
                                )
                                # Track earliest upcoming start time
                                if (
                                    earliest_upcoming is None
                                    or start < earliest_upcoming
                                ):
                                    earliest_upcoming = start

            except Exception as e:
                print(f"Skipping game due to error: {e}")
                continue

        return current, upcoming, earliest_upcoming

    except Exception as e:
        print("API Error:", e)
        return [], [], None


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []

    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except:
        return []


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def send_notification(new_games, upcoming):
    if not new_games and not upcoming:
        return

    message = (
        "🎮 **最新免费**\n"
        + "\n".join(
            f"- [{game['title']}]({game['url']}) (截止：{game['end_date']})"
            for game in new_games
        )
        if new_games
        else "🎮 暂无新的免费游戏\n"
    )

    if upcoming:
        message += "\n\n⏳ **即将免费**\n" + "\n".join(
            f"- [{game['title']}]({game['url']}) (开始：{game['start_date']})"
            for game in upcoming
        )

    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
            data={"title": "Epic免费游戏提醒", "desp": message},
            timeout=10,
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")


def log(msg):
    tz = ZoneInfo(TIME_ZONE)
    print(f"{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')} - {msg}")


def check():
    cached = load_cache()
    current, upcoming, earliest_upcoming = get_free_games()

    new_games = [g for g in current if g not in cached]

    if new_games or not cached:
        send_notification(new_games if new_games else current, upcoming)
        save_cache(current)
        log("New games found")
    else:
        log("No new games")

    return earliest_upcoming


def sleep_until(target_dt_or_hour, minute=None, second=0):
    """Sleep until target datetime or daily time.

    Usage:
        sleep_until(datetime_obj)  # Sleep until specific datetime
        sleep_until(11, 10)        # Sleep until 11:10 today/tomorrow
    """
    tz = ZoneInfo(TIME_ZONE)
    now = datetime.now(tz)

    if minute is not None:  # Called as sleep_until(hour, minute, second)
        hour = target_dt_or_hour
        target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        # If time already passed today → go to tomorrow
        if target <= now:
            target += timedelta(days=1)
    else:  # Called as sleep_until(datetime_obj)
        target = target_dt_or_hour
        if target.tzinfo is None:
            # Naive datetime → assume it's UTC
            target = target.replace(tzinfo=timezone.utc)
        # Convert to Toronto time
        target = target.astimezone(tz)

        # If time already passed → log and return
        if target <= now:
            log(f"Target time {target} is in the past")
            return

    seconds = (target - now).total_seconds()
    log(
        f"Sleeping until {target.strftime('%Y-%m-%d %H:%M:%S %Z')} ({seconds:.0f} seconds)"
    )
    time.sleep(seconds)


# run forever
while True:
    earliest_upcoming = check()

    if earliest_upcoming:
        # Sleep until the upcoming promotion + 10 minutes
        target_time = earliest_upcoming + timedelta(minutes=10)
        sleep_until(target_time)
    else:
        # No upcoming games found, sleep until 11:10 today/tomorrow
        sleep_until(11, 10)
