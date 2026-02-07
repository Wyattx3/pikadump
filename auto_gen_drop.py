"""
Auto Gen Drop - Real-time Monitoring + Pattern-based Generation + Auto Posting
Monitors Telegram channels, learns patterns from real cards, and drops generated cards
Always-on 24/7 system with periodic generation
"""
import asyncio
import sys
import os
import csv
import json
from pathlib import Path
from datetime import datetime
import random

# Fix Windows console encoding
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
from smart_generator import SmartGenerator, refresh_patterns

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Check if running on Replit
IS_REPLIT = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT') is not None

if IS_REPLIT:
    try:
        from keep_alive import keep_alive
        KEEP_ALIVE_AVAILABLE = True
    except ImportError:
        KEEP_ALIVE_AVAILABLE = False
else:
    KEEP_ALIVE_AVAILABLE = False

# ==================== CONFIGURATION ====================
CHANNEL_USERNAME = "pikadump"  # Channel to post to
CARDS_FILE = Path("output/cards.json")
BIN_DATABASE_FILE = Path("bin-list-data.csv")

# Generation settings
GENERATION_ENABLED = True
GENERATION_INTERVAL = 300  # seconds (5 minutes)
CARDS_PER_DROP = 5  # Cards to generate per drop
MIN_CARDS_TO_LEARN = 50  # Minimum cards before starting generation

# Image settings
IMAGE_PATH = Path("card_image.webp") if Path("card_image.webp").exists() else Path("card_image.jpg")
CONVERTED_IMAGE = Path("temp_image.jpg")

# ==================== GLOBAL VARIABLES ====================
BIN_DB = {}
card_detector = CardDetector()
smart_gen = None
posted_cards = set()
collected_cards = []

stats = {
    "found": 0,
    "posted": 0,
    "generated": 0,
    "gen_posted": 0,
    "duplicates": 0
}

COUNTRY_FLAGS = {
    "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺", "DE": "🇩🇪",
    "FR": "🇫🇷", "IT": "🇮🇹", "ES": "🇪🇸", "JP": "🇯🇵", "CN": "🇨🇳",
    "IN": "🇮🇳", "BR": "🇧🇷", "MX": "🇲🇽", "RU": "🇷🇺", "KR": "🇰🇷",
    "SG": "🇸🇬", "HK": "🇭🇰", "TW": "🇹🇼", "MY": "🇲🇾", "TH": "🇹🇭",
}


def load_bin_database():
    """Load BIN database from CSV"""
    global BIN_DB
    if not BIN_DATABASE_FILE.exists():
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
                    }
        print(f"[OK] Loaded {len(BIN_DB)} BINs")
    except Exception as e:
        print(f"[X] Error loading BIN: {e}")


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
    
    first_digit = card_number[0] if card_number else '0'
    
    if first_digit == '4':
        return {"bank": "VISA BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "VISA", "level": "CLASSIC"}
    elif first_digit == '5':
        return {"bank": "MASTERCARD BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "MASTERCARD", "level": "STANDARD"}
    elif first_digit == '3':
        return {"bank": "AMEX BANK", "country": "US", "flag": "🇺🇸", "type": "CREDIT", "brand": "AMEX", "level": "GOLD"}
    
    return {"bank": "UNKNOWN BANK", "country": "XX", "flag": "🏳️", "type": "CREDIT", "brand": "UNKNOWN", "level": "STANDARD"}


def convert_image(webp_path: Path, jpg_path: Path) -> bool:
    """Convert webp to jpg"""
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


def format_card_message(card: dict, is_generated: bool = False) -> str:
    """Format card for posting"""
    card_number = card.get('card_number', '')
    month = card.get('expiry_month')
    year = card.get('expiry_year')
    cvv = card.get('cvv', '')
    
    bin_info = get_bin_info(card_number)
    bin_6 = card_number[:6]
    
    if month and year and cvv:
        if isinstance(month, int):
            card_line = f"{card_number}|{month:02d}|{year}|{cvv}"
        else:
            card_line = f"{card_number}|{month}|{year}|{cvv}"
    else:
        card_line = card_number
    
    tag = "🎲 GEN" if is_generated else "🔍 FOUND"
    
    message = f"""Pika Fined Cashtho ~ʕ⁠っ⁠•⁠ᴥ⁠•⁠ʔ⁠っ {tag}

<b>{bin_info['brand']} • {bin_info['type']} • {bin_info['level']}</b>

<code>{card_line}</code>

{bin_info['bank']} | {bin_info['country']} {bin_info['flag']}
BIN: {bin_6}

pika father @kokakeki"""
    
    return message


def save_card_to_json(card: dict):
    """Save card to JSON file for pattern learning"""
    global collected_cards
    
    collected_cards.append(card)
    
    # Also save to file
    cards = []
    if CARDS_FILE.exists():
        try:
            with open(CARDS_FILE, 'r', encoding='utf-8') as f:
                cards = json.load(f)
        except:
            cards = []
    
    cards.append(card)
    
    CARDS_FILE.parent.mkdir(exist_ok=True)
    with open(CARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)


def init_generator():
    """Initialize the smart generator"""
    global smart_gen
    
    smart_gen = SmartGenerator(str(CARDS_FILE))
    cards = smart_gen.load_cards()
    
    if len(cards) >= MIN_CARDS_TO_LEARN:
        smart_gen.build_patterns(cards)
        print(f"[OK] Generator initialized with {len(cards)} cards")
        return True
    else:
        print(f"[!] Need {MIN_CARDS_TO_LEARN - len(cards)} more cards before generation")
        return False


# ==================== PYROGRAM CLIENT ====================
app = Client(
    SESSION_NAME,
    api_id=int(API_ID),
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER if PHONE_NUMBER else None
)


@app.on_message(filters.channel | filters.group)
async def handle_message(client: Client, message: Message):
    """Handle incoming messages - extract and save cards"""
    global stats
    
    text_content = message.text or message.caption or ""
    
    try:
        # Skip our own channel
        if message.chat and message.chat.username:
            if message.chat.username.lower() == CHANNEL_USERNAME.lower():
                return
        
        if not text_content:
            return
        
        cards = card_detector.parse_message(text_content)
        
        if not cards:
            return
    except Exception:
        return
    
    stats["found"] += len(cards)
    source = message.chat.title or message.chat.username or f"Chat {message.chat.id}"
    
    for card in cards:
        card_number = card.get('card_number', '')
        card_key = f"{card_number}_{card.get('expiry_month')}_{card.get('expiry_year')}"
        
        if card_key in posted_cards:
            stats["duplicates"] += 1
            continue
        
        try:
            # Save for pattern learning
            save_card_to_json(card)
            
            # Post to channel
            msg = format_card_message(card, is_generated=False)
            
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
            
            posted_cards.add(card_key)
            stats["posted"] += 1
            
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] 🔍 Posted FOUND: {card_number[:6]}****** from '{source}'")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"[X] Error posting: {e}")


async def generation_loop(client: Client):
    """Background loop that periodically generates and drops cards"""
    global smart_gen, stats
    
    print(f"[+] Generation loop started (interval: {GENERATION_INTERVAL}s)")
    
    while True:
        await asyncio.sleep(GENERATION_INTERVAL)
        
        if not GENERATION_ENABLED:
            continue
        
        # Refresh patterns periodically
        cards = smart_gen.load_cards() if smart_gen else []
        
        if len(cards) < MIN_CARDS_TO_LEARN:
            print(f"[!] Waiting for more cards ({len(cards)}/{MIN_CARDS_TO_LEARN})")
            continue
        
        # Refresh patterns
        if smart_gen:
            smart_gen.build_patterns(cards)
        else:
            init_generator()
            if not smart_gen:
                continue
        
        # Generate cards
        generated = smart_gen.generate_cards(CARDS_PER_DROP)
        
        if not generated:
            continue
        
        print(f"\n[+] Generated {len(generated)} cards, dropping...")
        
        for card in generated:
            card_number = card['card_number']
            card_key = f"{card_number}_{card['expiry_month']}_{card['expiry_year']}"
            
            if card_key in posted_cards:
                continue
            
            try:
                msg = format_card_message(card, is_generated=True)
                
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
                
                posted_cards.add(card_key)
                stats["generated"] += 1
                stats["gen_posted"] += 1
                
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] 🎲 Posted GEN: {card_number[:6]}****** [{card['card_type']}]")
                
                # Random delay between posts
                await asyncio.sleep(random.uniform(3, 8))
                
            except Exception as e:
                print(f"[X] Error posting generated card: {e}")
        
        print(f"[OK] Drop complete. Total generated: {stats['gen_posted']}")


async def main():
    """Main application entry"""
    global smart_gen
    
    print("\n" + "=" * 70)
    print("   🚀 Auto Gen Drop - Monitor + Generate + Post")
    print("   Pikadump Telegram Bot - Always On 24/7")
    print("=" * 70)
    print(f"   Target Channel: @{CHANNEL_USERNAME}")
    print(f"   Generation: {'ENABLED' if GENERATION_ENABLED else 'DISABLED'}")
    print(f"   Generation Interval: {GENERATION_INTERVAL}s")
    print(f"   Cards Per Drop: {CARDS_PER_DROP}")
    if IS_REPLIT:
        print("   Mode: Replit 24/7")
    print("=" * 70)
    
    # Start keep-alive for Replit
    if IS_REPLIT and KEEP_ALIVE_AVAILABLE:
        keep_alive()
    
    # Load BIN database
    load_bin_database()
    
    # Convert image
    if IMAGE_PATH.exists() and IMAGE_PATH.suffix.lower() == '.webp':
        print("[+] Converting image...")
        if convert_image(IMAGE_PATH, CONVERTED_IMAGE):
            print("[OK] Image ready")
    
    # Initialize generator
    print("\n[+] Initializing Smart Generator...")
    init_generator()
    
    print("\n[+] Starting Telegram client...")
    
    try:
        await app.start()
        me = await app.get_me()
        print(f"[OK] Logged in as: {me.first_name} (@{me.username or 'N/A'})")
        
        # Cache dialogs
        print("[+] Caching dialogs...")
        dialog_count = 0
        async for dialog in app.get_dialogs():
            dialog_count += 1
        print(f"[OK] Cached {dialog_count} dialogs")
        
        print("\n" + "-" * 70)
        print("[+] Listening for cards in all channels/groups...")
        print("[+] Press Ctrl+C to stop")
        print("-" * 70 + "\n")
        
        # Start generation loop in background
        if GENERATION_ENABLED:
            asyncio.create_task(generation_loop(app))
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        pass
    finally:
        print("\n" + "-" * 70)
        print("   📊 Final Statistics")
        print("-" * 70)
        print(f"   Cards Found:      {stats['found']}")
        print(f"   Cards Posted:     {stats['posted']}")
        print(f"   Cards Generated:  {stats['generated']}")
        print(f"   Gen Posted:       {stats['gen_posted']}")
        print(f"   Duplicates:       {stats['duplicates']}")
        print("-" * 70)
        await app.stop()
        print("[OK] Stopped.")


if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        print("\n[OK] Application closed.")
        sys.exit(0)
