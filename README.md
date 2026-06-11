# Epic Free Games Notifier 🎮

[English](README.md) | [简体中文](README_zh.md)

Get automated notifications for free games on the Epic Games Store, delivered via [Server酱](https://sct.ftqq.com/) to your WeChat.

![Example Notification](https://github.com/user-attachments/assets/1a82c313-7407-4679-9abd-8da7d51c068d)
*(Example notification showing current and upcoming games)*

## Features ✨
- ✅ **Smart continuous checking** - runs 24/7 with intelligent sleep scheduling
- 🔍 Clear separation between **claimable now** vs **coming soon**
- 💾 Automatic caching prevents duplicate alerts
- 🎮 Perfect for **Pterodactyl/Jexactyl** game panel hosting
- 🏃 No external dependencies - entirely self-contained

## How It Works 🔄

The notifier runs continuously and intelligently:
1. **Checks for free games** every time it wakes up
2. **Smart notifications**:
   - Sends alerts only when **new current free games** appear (vs cache)
   - Always shows **upcoming games** for reference
   - Cache updates automatically when new current games are detected
3. **Intelligent sleep** scheduling:
   - If upcoming games exist: sleeps until the earliest upcoming game starts + 10 minutes
   - If no upcoming games: sleeps until the next 11:10 (configurable)
4. **Runs forever** - perfect for always-on hosting like Pterodactyl/Jexactyl

## Setup for Pterodactyl/Jexactyl 🚀

### Step 1️⃣: Get Your Server酱 Key
1. Visit [Server酱](https://sct.ftqq.com/) (login with GitHub)
2. Copy your `SendKey` (looks like `SCT123456...`)

### Step 2️⃣: Configure the Notifier
In `app.py`, replace the placeholder key with your actual key:
```python
SERVER_CHAN_KEY = "YOUR_ACTUAL_SENDKEY_HERE"
```

Optionally, adjust the timezone and daily check time:
```python
TIME_ZONE = "UTC"  # Change to your timezone
sleep_until(11, 10)             # Daily Check at 11:10
```

### Step 3️⃣: Set Up on Your Game Panel

**For Pterodactyl/Jexactyl:**
1. Create a new "Server" in your game panel
2. Upload these files to the server:
   - `app.py`
   - `requirements.txt`
3. Make sure your startup command and settings points to the right files
4. Start the server - it will run continuously

### Step 4️⃣: Verify It's Working
- Check the **console output** in your panel
- You should see logs like:
  ```
  2026-06-07 11:10:00 EST - New games found
  Sleeping until 2026-06-12 12:34:56 EST (432000 seconds)
  ```

## Troubleshooting 🛠️

| Symptom | Fix |
|---------|-----|
| No notifications | 1. Test Server酱 key manually:<br>`curl -X POST "https://sctapi.ftqq.com/YOUR_KEY.send" -d "title=Test&desp=Hello"`<br>2. Check server console output |
| ImportError: No module named 'requests' | Run: `pip install requests` (or let your panel install from requirements.txt) |
| Wrong games shown | Delete `games_cache.json` from server storage, then restart |
| API errors | Wait 1 hour (Epic sometimes rate-limits) |

## Advanced Configuration ⚙️

**Change daily check time:**
Edit the last `sleep_until()` call in `app.py`:
```python
sleep_until(16, 30)  # Changes from 11:10 to 16:30 (UTC based on your TZ)
```

**Change timezone:**
```python
TIME_ZONE = "Europe/London"  # List of timezones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

**Change check delays:**
Modify the earliest upcoming game offset:
```python
target_time = earliest_upcoming + timedelta(minutes=20)  # Changed from 10 to 20 minutes
```

## Requirements 📦

- Python 3.9+
- `requests` library (see `requirements.txt`)
- Internet connection
- Active Server酱 account

---

Enjoy your free games! 🎁  
*Consider starring this repo if you find it useful!*
