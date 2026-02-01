"""
Auto Drop - Real-time Card Monitoring and Posting
Monitors all channels/groups and automatically posts found cards to @pikadump
"""
import asyncio
import sys
import os
import csv
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding and buffering
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    os.environ['PYTHONUNBUFFERED'] = '1'

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER
from card_detector import CardDetector

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Check if running on Replit
IS_REPLIT = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT') is not None

# Import keep_alive for Replit
if IS_REPLIT:
    try:
        from keep_alive import keep_alive
        KEEP_ALIVE_AVAILABLE = True
    except ImportError:
        KEEP_ALIVE_AVAILABLE = False
else:
    KEEP_ALIVE_AVAILABLE = False

# Configuration
CHANNEL_USERNAME = "pikadump"  # Channel to post to

# Image path - check multiple locations
def get_image_path():
    """Find the image in multiple possible locations"""
    possible_paths = [
        Path("card_image.webp"),  # Replit - same directory
        Path("card_image.jpg"),   # Replit - already converted
        Path(r"C:\Users\Administrator\Desktop\1769984384062.webp"),  # Windows original
    ]
    for p in possible_paths:
        if p.exists():
            return p
    return Path("card_image.webp")  # Default for Replit

IMAGE_PATH = get_image_path()
CONVERTED_IMAGE = Path("temp_image.jpg")
BIN_DATABASE_FILE = Path("bin-list-data.csv")

# Country flag emojis
COUNTRY_FLAGS = {
    "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺", "DE": "🇩🇪",
    "FR": "🇫🇷", "IT": "🇮🇹", "ES": "🇪🇸", "JP": "🇯🇵", "CN": "🇨🇳",
    "IN": "🇮🇳", "BR": "🇧🇷", "MX": "🇲🇽", "RU": "🇷🇺", "KR": "🇰🇷",
    "SG": "🇸🇬", "HK": "🇭🇰", "TW": "🇹🇼", "MY": "🇲🇾", "TH": "🇹🇭",
    "ID": "🇮🇩", "PH": "🇵🇭", "VN": "🇻🇳", "NL": "🇳🇱", "BE": "🇧🇪",
    "CH": "🇨🇭", "AT": "🇦🇹", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰",
    "FI": "🇫🇮", "PL": "🇵🇱", "CZ": "🇨🇿", "PT": "🇵🇹", "GR": "🇬🇷",
    "TR": "🇹🇷", "AE": "🇦🇪", "SA": "🇸🇦", "IL": "🇮🇱", "ZA": "🇿🇦",
    "NG": "🇳🇬", "EG": "🇪🇬", "AR": "🇦🇷", "CL": "🇨🇱", "CO": "🇨🇴",
    "NZ": "🇳🇿", "IE": "🇮🇪", "PK": "🇵🇰", "BD": "🇧🇩", "UA": "🇺🇦",
}

# Global variables
BIN_DB = {}
card_detector = CardDetector()
posted_cards = set()  # Track posted cards to avoid duplicates
stats = {"found": 0, "posted": 0, "duplicates": 0}


def load_bin_database():
    """Load BIN database from CSV file"""
    global BIN_DB
    if not BIN_DATABASE_FILE.exists():
        print(f"[!] BIN database not found: {BIN_DATABASE_FILE}")
        return
    
    try:
        with open(BIN_DATABASE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bin_num = row.get('BIN', '').strip()
                if bin_num:
                    BIN_DB[bin_num] = {
                        'brand': row.get('Brand', 'UNKNOWN').upper(),
                        'type': row.get('Type', 'CREDIT').upper(),
                        'category': row.get('Category', 'STANDARD').upper() or 'STANDARD',
                        'issuer': row.get('Issuer', 'UNKNOWN BANK').upper(),
                        'country': row.get('isoCode2', 'XX'),
                        'country_name': row.get('CountryName', 'UNKNOWN'),
                    }
        print(f"[OK] Loaded {len(BIN_DB)} BINs from database")
    except Exception as e:
        print(f"[X] Error loading BIN database: {e}")


def get_bin_info(card_number: str) -> dict:
    """Get BIN info from card number"""
    bin_6 = card_number[:6]
    
    if bin_6 in BIN_DB:
        info = BIN_DB[bin_6]
        country = info['country']
        flag = COUNTRY_FLAGS.get(country, "🏳️")
        return {
            "bank": info['issuer'],
            "country": country,
            "flag": flag,
            "type": info['type'],
            "brand": info['brand'],
            "level": info['category']
        }
    
    # Default based on card type
    first_digit = card_number[0] if card_number else '0'
    
    if first_digit == '4':
        return {"bank": "VISA BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "VISA", "level": "CLASSIC"}
    elif first_digit == '5':
        return {"bank": "MASTERCARD BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "MASTERCARD", "level": "STANDARD"}
    elif first_digit == '3':
        return {"bank": "AMEX BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "AMEX", "level": "GOLD"}
    elif first_digit == '6':
        return {"bank": "DISCOVER BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "DISCOVER", "level": "STANDARD"}
    
    return {"bank": "UNKNOWN BANK", "country": "XX", "flag": "🏳️", "type": "CREDIT", "brand": "UNKNOWN", "level": "STANDARD"}


def convert_webp_to_jpg(webp_path: Path, jpg_path: Path) -> bool:
    """Convert webp image to jpg"""
    if not PIL_AVAILABLE:
        return False
    try:
        img = Image.open(webp_path)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(jpg_path, 'JPEG', quality=95)
        return True
    except:
        return False


def format_card_message(card: dict) -> str:
    """Format card info into message"""
    card_number = card.get('card_number', '')
    month = card.get('expiry_month')
    year = card.get('expiry_year')
    cvv = card.get('cvv', '')
    
    bin_info = get_bin_info(card_number)
    bin_6 = card_number[:6]
    
    # Build card line
    if month and year and cvv:
        card_line = f"{card_number}|{month:02d}|{year}|{cvv}"
    elif month and year:
        card_line = f"{card_number}|{month:02d}|{year}"
    else:
        card_line = card_number
    
    message = f"""Pika Fined Cashtho ~ʕ⁠っ⁠•⁠ᴥ⁠•⁠ʔ⁠っ

<b>{bin_info['brand']} • {bin_info['type']} • {bin_info['level']}</b>

<code>{card_line}</code>

{bin_info['bank']} | {bin_info['country']} {bin_info['flag']}
BIN: {bin_6}

pika father @kokakeki"""
    
    return message


# Create client using existing session
app = Client(
    SESSION_NAME,
    api_id=int(API_ID),
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER if PHONE_NUMBER else None
)


@app.on_message(filters.channel | filters.group)
async def handle_message(client: Client, message: Message):
    """Handle incoming messages from channels/groups"""
    global stats
    
    # Get text from message.text OR message.caption (for images/photos)
    text_content = message.text or message.caption or ""
    
    try:
        # Skip messages from our own channel
        if message.chat and message.chat.username and message.chat.username.lower() == CHANNEL_USERNAME.lower():
            return
        
        # Skip if no text or caption
        if not text_content:
            return
        
        # Extract cards from text or caption
        cards = card_detector.parse_message(text_content)
        
        if not cards:
            return
    except Exception:
        return
    
    stats["found"] += len(cards)
    
    # Get source info
    source = message.chat.title or message.chat.username or f"Chat {message.chat.id}"
    
    # Process each card
    for card in cards:
        card_number = card.get('card_number', '')
        
        # Check if already posted
        card_key = f"{card_number}_{card.get('expiry_month')}_{card.get('expiry_year')}"
        if card_key in posted_cards:
            stats["duplicates"] += 1
            print(f"[!] Duplicate skipped: {card_number[:6]}******")
            continue
        
        try:
            # Format message
            msg = format_card_message(card)
            
            # Post to channel
            if CONVERTED_IMAGE.exists():
                await client.send_photo(
                    chat_id=f"@{CHANNEL_USERNAME}",
                    photo=str(CONVERTED_IMAGE),
                    caption=msg,
                    parse_mode=ParseMode.HTML
                )
            else:
                await client.send_message(
                    chat_id=f"@{CHANNEL_USERNAME}",
                    text=msg,
                    parse_mode=ParseMode.HTML
                )
            
            # Mark as posted
            posted_cards.add(card_key)
            stats["posted"] += 1
            
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] [OK] Posted: {card_number[:6]}****** from '{source}'")
            
            # Small delay to avoid flood
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"[X] Error posting card: {e}")
            continue


async def main():
    print("\n" + "=" * 60)
    print("   Auto Drop - Real-time Card Monitor & Poster")
    print("=" * 60)
    print(f"   Target Channel: @{CHANNEL_USERNAME}")
    if IS_REPLIT:
        print("   Mode: Replit 24/7")
    print("=" * 60)
    
    # Start keep-alive server for Replit
    if IS_REPLIT and KEEP_ALIVE_AVAILABLE:
        keep_alive()
    
    # Load BIN database
    load_bin_database()
    
    # Convert image if needed
    if IMAGE_PATH.exists() and IMAGE_PATH.suffix.lower() == '.webp':
        print("[+] Converting image...")
        if convert_webp_to_jpg(IMAGE_PATH, CONVERTED_IMAGE):
            print("[OK] Image ready")
        else:
            print("[!] Image conversion failed, will post without image")
    
    print("\n[+] Starting real-time monitoring...")
    print("[+] Listening for cards in all channels/groups...")
    print("[+] Press Ctrl+C to stop\n")
    print("-" * 60)
    
    try:
        await app.start()
        me = await app.get_me()
        print(f"[OK] Logged in as: {me.first_name} (@{me.username or 'N/A'})")
        
        # Cache all dialogs to avoid peer resolution errors
        print("[+] Caching dialogs...")
        dialog_count = 0
        async for dialog in app.get_dialogs():
            dialog_count += 1
        print(f"[OK] Cached {dialog_count} dialogs")
        print("-" * 60 + "\n")
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        pass
    finally:
        print("\n" + "-" * 60)
        print(f"   Cards Found: {stats['found']}")
        print(f"   Cards Posted: {stats['posted']}")
        print(f"   Duplicates Skipped: {stats['duplicates']}")
        print("-" * 60)
        await app.stop()
        print("[OK] Stopped.")


if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        print("\n[OK] Application closed.")
        sys.exit(0)
