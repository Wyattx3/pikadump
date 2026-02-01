"""
Message Handler
Handles real-time message monitoring and card extraction
"""
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from typing import List, Set
from card_detector import CardDetector
from data_manager import DataManager
from config import ALLOWED_CARD_TYPES


class MessageHandler:
    """Handles message processing and card extraction"""
    
    def __init__(self, client: Client, monitored_chats: List[int]):
        self.client = client
        self.monitored_chats = set(monitored_chats)
        self.card_detector = CardDetector()
        self.data_manager = DataManager()
        self.processed_messages: Set[int] = set()
        self.cards_found_count = 0
    
    def should_process_message(self, message: Message) -> bool:
        """Check if message should be processed"""
        # Only process messages from monitored chats
        if message.chat.id not in self.monitored_chats:
            return False
        
        # Skip if already processed
        if message.id in self.processed_messages:
            return False
        
        # Only process text messages
        if not message.text:
            return False
        
        return True
    
    def filter_by_card_type(self, cards: List[dict]) -> List[dict]:
        """Filter cards by allowed card types"""
        if not ALLOWED_CARD_TYPES:
            return cards
        
        return [
            card for card in cards
            if card.get('card_type') in ALLOWED_CARD_TYPES
        ]
    
    async def process_message(self, message: Message):
        """Process a single message and extract cards"""
        if not self.should_process_message(message):
            return
        
        try:
            # Extract text
            text = message.text or ""
            
            if not text.strip():
                return
            
            # Extract cards
            cards = self.card_detector.parse_message(text)
            
            # Filter by card type if specified
            cards = self.filter_by_card_type(cards)
            
            if not cards:
                return
            
            # Get chat info
            chat_title = message.chat.title or message.chat.username or f"Chat {message.chat.id}"
            
            # Save each card
            for card_info in cards:
                saved = self.data_manager.save_card(
                    card_info,
                    source_channel=chat_title
                )
                
                if saved:
                    self.cards_found_count += 1
                    print(f"\n[OK] Card တွေ့ရှိပါပြီ! ({self.cards_found_count} total)")
                    print(f"    Type: {card_info.get('card_type')}")
                    print(f"    Number: {card_info.get('card_number')}")
                    print(f"    Source: {chat_title}")
                else:
                    print(f"\n[!] Duplicate card detected: {card_info.get('card_number')}")
            
            # Mark as processed
            self.processed_messages.add(message.id)
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    async def process_history(self, chat_id: int, limit: int = None):
        """Process message history from a chat"""
        try:
            print(f"\n[+] Processing message history from chat {chat_id}...")
            count = 0
            
            async for message in self.client.get_chat_history(chat_id, limit=limit):
                await self.process_message(message)
                count += 1
                
                # Print progress every 100 messages
                if count % 100 == 0:
                    print(f"    Processed {count} messages...")
            
            print(f"[OK] Finished processing {count} messages from chat {chat_id}")
            
        except Exception as e:
            print(f"Error processing history for chat {chat_id}: {e}")
    
    async def process_last_message(self, chat_id: int):
        """Process only the last message from a chat"""
        try:
            async for message in self.client.get_chat_history(chat_id, limit=1):
                await self.process_message(message)
                return message
        except Exception as e:
            print(f"Error processing last message for chat {chat_id}: {e}")
            return None
    
    async def start_monitoring(self):
        """Start real-time message monitoring"""
        print("\n[+] Real-time monitoring စတင်ပါပြီ...")
        print("    Press Ctrl+C to stop\n")
        
        @self.client.on_message()
        async def handle_message(client: Client, message: Message):
            await self.process_message(message)
        
        # Keep running
        await self.client.idle()
    
    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            'cards_found': self.cards_found_count,
            'messages_processed': len(self.processed_messages),
            'monitored_chats': len(self.monitored_chats)
        }
