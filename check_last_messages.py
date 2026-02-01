"""
Check Last Messages Only
Extracts cards from the last message of each channel/group
"""
import asyncio
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from telegram_client import TelegramClient
from card_detector import CardDetector
from data_manager import DataManager


async def main():
    print("\n" + "=" * 60)
    print("   Telegram Card Extractor - Last Message Only")
    print("=" * 60)
    
    # Initialize
    telegram_client = TelegramClient()
    card_detector = CardDetector()
    data_manager = DataManager()
    
    try:
        # Authenticate
        print("\n[+] Authenticating...")
        auth_success = await telegram_client.authenticate()
        
        if not auth_success:
            print("[X] Authentication failed.")
            return
        
        # Connect
        await telegram_client.connect()
        
        # Get channels and groups
        print("\n[+] Getting channels and groups...")
        chats = await telegram_client.get_channels_and_groups()
        
        if not chats:
            print("[X] No channels/groups found.")
            return
        
        print(f"[OK] Found {len(chats)} channels/groups")
        
        # Process last message from each chat
        total_cards = 0
        client = telegram_client.get_client()
        
        print("\n[+] Checking last message from each channel/group...\n")
        
        for chat in chats:
            chat_id = chat['id']
            chat_title = chat['title']
            
            try:
                # Get last message only
                async for message in client.get_chat_history(chat_id, limit=1):
                    if message.text:
                        # Extract cards
                        cards = card_detector.parse_message(message.text)
                        
                        for card_info in cards:
                            saved = data_manager.save_card(card_info, source_channel=chat_title)
                            if saved:
                                total_cards += 1
                                print(f"[OK] Card found in '{chat_title}'")
                                print(f"     Type: {card_info.get('card_type')}")
                                print(f"     Number: {card_info.get('card_number')}")
                                if card_info.get('expiry_month'):
                                    print(f"     Expiry: {card_info.get('expiry_month'):02d}/{card_info.get('expiry_year')}")
                                if card_info.get('cvv'):
                                    print(f"     CVV: {card_info.get('cvv')}")
                                print()
                        
            except Exception as e:
                print(f"[!] Error checking '{chat_title}': {e}")
                continue
        
        # Summary
        print("\n" + "=" * 60)
        print(f"   Total Cards Found: {total_cards}")
        print("=" * 60)
        
        if total_cards > 0:
            print(f"\n[OK] Cards saved to:")
            print(f"     - output/cards.csv")
            print(f"     - output/cards.json")
            print(f"     - output/cards.txt")
        
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
    except Exception as e:
        print(f"[X] Error: {e}")
    finally:
        await telegram_client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[OK] Application closed.")
        sys.exit(0)
