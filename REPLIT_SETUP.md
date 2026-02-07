# Replit Setup Guide - Auto Gen Drop Bot

## Features

- 🔍 Real-time card scraping from all Telegram channels/groups
- 🎲 Smart pattern-based card generation (learns from 53,000+ real cards)
- 📤 Auto drop to @pikadump channel every 2 seconds
- 🌐 24/7 uptime with keep-alive server

## Step 1: Create New Replit

1. Go to [replit.com](https://replit.com)
2. Click **Create Repl**
3. Choose **Import from GitHub**
4. Paste: `https://github.com/Wyattx3/pikadump`
5. Click **Import**

Or manually:
1. Select **Python** template
2. Upload all files from this repo

## Step 2: Set Secrets (Environment Variables)

Go to **Secrets** tab (🔒 lock icon) and add:

| Key | Value |
|-----|-------|
| `API_ID` | Your Telegram API ID |
| `API_HASH` | Your Telegram API Hash |
| `PHONE_NUMBER` | Your phone number (+959...) |

Get API credentials from: https://my.telegram.org/apps

## Step 3: Upload Cards Data

Upload `output/cards.json` with your scraped cards data for pattern learning.
The smart generator needs this file to learn patterns from real cards.

## Step 4: First Run - Authentication

1. Click **Run** button
2. Wait for dependencies to install
3. Enter verification code when prompted (sent to Telegram)
4. Enter 2FA password if you have one
5. Session file will be created automatically

## Step 5: Enable 24/7 Uptime

### Option A: Replit Core Plan (Recommended)
1. Go to Repl Settings
2. Enable **Always On** toggle

### Option B: Free Plan with UptimeRobot
1. Copy your Replit URL (e.g., `https://your-repl.username.repl.co`)
2. Go to [uptimerobot.com](https://uptimerobot.com)
3. Create free account
4. Add new monitor:
   - Monitor Type: HTTP(s)
   - URL: Your Replit URL
   - Monitoring Interval: 5 minutes
5. This will ping your Repl every 5 minutes to keep it alive

## Configuration

Edit `auto_gen_drop.py` to customize:

```python
GENERATION_INTERVAL = 2      # Generate every 2 seconds
CARDS_PER_DROP = 1           # 1 card per drop
INITIAL_GEN_DELAY = 2        # Start after 2 seconds
```

## Files Description

| File | Description |
|------|-------------|
| `auto_gen_drop.py` | Main bot - scrape + generate + drop |
| `smart_generator.py` | Pattern-based card generator |
| `card_detector.py` | Card detection from messages |
| `keep_alive.py` | Web server for 24/7 uptime |
| `config.py` | Configuration settings |
| `bin-list-data.csv` | BIN database (374,788 BINs) |
| `output/cards.json` | Scraped cards for pattern learning |

## How It Works

1. **Scrape Mode**: Monitors all channels/groups for new cards
   - When found → immediately drops to @pikadump
   - Saves to `output/cards.json` for pattern learning

2. **Generate Mode**: When no scrape activity
   - Uses smart generator (learns from 53,000+ real cards)
   - Generates cards with diverse BINs, CVVs, expiry dates
   - Drops every 2 seconds

3. **Pattern Learning**:
   - 8-digit prefix patterns from real cards
   - Suffix digit frequency at each position
   - CVV/Month/Year distribution analysis

## Troubleshooting

### Bot stops running
- Check UptimeRobot is active
- Check Replit console for errors
- Restart the Repl

### "Need more cards before generation"
- Upload `output/cards.json` with at least 50 cards
- Or wait for scraping to collect cards

### Session expired
- Delete `telegram_card_extractor.session`
- Re-run and authenticate again

### Cards not posting
- Make sure you're admin of @pikadump channel
- Check API credentials are correct

## Support

Check console for error messages. The bot logs all activity.
