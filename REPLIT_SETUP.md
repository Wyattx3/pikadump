# Replit Setup Guide - Auto Drop Bot (Core Plan)

## Step 1: Create New Replit

1. Go to [replit.com](https://replit.com)
2. Click **Create Repl**
3. Select **Python** template
4. Name it: `auto-drop-bot`

## Step 2: Upload Files

Upload these files to your Replit:

```
auto_drop.py
card_detector.py
config.py
data_manager.py
requirements.txt
bin-list-data.csv
card_image.webp
.replit
replit.nix
```

## Step 3: Set Secrets (Environment Variables)

Go to **Secrets** tab (lock icon on left sidebar) and add:

| Key | Value |
|-----|-------|
| `API_ID` | Your Telegram API ID |
| `API_HASH` | Your Telegram API Hash |
| `PHONE_NUMBER` | Your phone number (+959...) |

## Step 4: First Run - Authentication

1. Click **Run** button
2. Enter verification code when prompted
3. Enter 2FA password if you have one
4. Session file will be created automatically

## Step 5: Enable Always On (Core Plan)

1. Go to your Repl
2. Click on the **Repl name** at the top
3. Go to **Settings** tab
4. Find **Always On** toggle
5. Turn it **ON**

Done! Your bot will now run 24/7 without stopping.

## Troubleshooting

### Bot stops after a while
- Make sure UptimeRobot is pinging your Replit URL
- Check if Replit is sleeping (free tier limitation)

### Session expired
- Delete the session file and re-run
- Re-authenticate with your phone number

### Cards not posting
- Check if @pikadump channel exists
- Make sure you're an admin of the channel

## Files Description

| File | Description |
|------|-------------|
| `auto_drop.py` | Main bot script |
| `card_detector.py` | Card detection logic |
| `config.py` | Configuration settings |
| `keep_alive.py` | Web server for 24/7 uptime |
| `bin-list-data.csv` | BIN database |
| `card_image.webp` | Image for posts |

## Support

If you encounter issues, check the Replit console for error messages.
