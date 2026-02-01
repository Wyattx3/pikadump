"""
Telegram Client Setup
Handles Telegram API connection and authentication
"""
import asyncio
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, Unauthorized
from config import API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER


class TelegramClient:
    """Manages Telegram client connection and authentication"""
    
    def __init__(self):
        if not API_ID or not API_HASH:
            raise ValueError(
                "API_ID နဲ့ API_HASH ကို .env file မှာ သတ်မှတ်ပေးရပါမယ်။\n"
                "https://my.telegram.org/apps မှာ ရယူနိုင်ပါတယ်။"
            )
        
        self.client = Client(
            SESSION_NAME,
            api_id=int(API_ID),
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER if PHONE_NUMBER else None
        )
        self.is_connected = False
    
    async def connect(self):
        """Connect to Telegram"""
        try:
            await self.client.start()
            self.is_connected = True
            print("[OK] Telegram နဲ့ connect လုပ်ပြီးပါပြီ။")
            return True
        except Exception as e:
            print(f"[X] Connect လုပ်ရာမှာ error ဖြစ်ပါတယ်: {e}")
            return False
    
    async def authenticate(self):
        """Handle authentication (phone number login)"""
        try:
            # Try to start client - Pyrogram handles auth automatically
            print("\n=== Telegram Authentication ===")
            if PHONE_NUMBER:
                print(f"Phone number: {PHONE_NUMBER}")
            
            # Connect and check if we need to auth
            if not self.client.is_connected:
                await self.client.connect()
            
            # Check if already logged in by trying to get_me
            try:
                me = await self.client.get_me()
                print(f"[OK] Already logged in as: {me.first_name} (@{me.username or 'N/A'})")
                self.is_connected = True
                return True
            except Unauthorized:
                pass
            except Exception:
                pass
            
            # Need phone number login
            phone = PHONE_NUMBER
            if not phone:
                phone = input("Phone number ထည့်ပါ (country code ပါရပါမယ်): ").strip()
            
            # Send code
            print(f"\n[INFO] Sending verification code to {phone}...")
            sent_code = await self.client.send_code(phone)
            print("[OK] Verification code ပို့ပြီးပါပြီ။")
            
            # Get code from user input
            code = input("\nTelegram မှာ ရရှိထားတဲ့ code ထည့်ပါ: ").strip()
            
            # Sign in
            try:
                await self.client.sign_in(phone, sent_code.phone_code_hash, code)
                me = await self.client.get_me()
                print(f"[OK] Login အောင်မြင်ပါတယ်! Welcome {me.first_name}")
                self.is_connected = True
                return True
            except SessionPasswordNeeded:
                # 2FA password required
                print("\n[INFO] 2FA password လိုအပ်ပါတယ်။")
                password = input("2FA password ထည့်ပါ: ").strip()
                
                await self.client.check_password(password)
                me = await self.client.get_me()
                print(f"[OK] Login အောင်မြင်ပါတယ်! Welcome {me.first_name}")
                self.is_connected = True
                return True
                
        except Exception as e:
            print(f"[X] Authentication error: {e}")
            return False
    
    async def get_dialogs(self):
        """Get all dialogs (channels, groups, chats)"""
        if not self.is_connected:
            await self.connect()
        
        dialogs = []
        async for dialog in self.client.get_dialogs():
            dialogs.append({
                'id': dialog.chat.id,
                'title': dialog.chat.title or dialog.chat.first_name or "Unknown",
                'type': dialog.chat.type.name if hasattr(dialog.chat.type, 'name') else str(dialog.chat.type),
                'username': dialog.chat.username
            })
        
        return dialogs
    
    async def get_channels_and_groups(self):
        """Get only channels and groups"""
        dialogs = await self.get_dialogs()
        return [
            d for d in dialogs 
            if d['type'] in ['CHANNEL', 'SUPERGROUP', 'GROUP']
        ]
    
    async def get_chat_info(self, chat_id):
        """Get information about a specific chat"""
        try:
            chat = await self.client.get_chat(chat_id)
            return {
                'id': chat.id,
                'title': chat.title or chat.first_name or "Unknown",
                'type': chat.type.name if hasattr(chat.type, 'name') else str(chat.type),
                'username': chat.username,
                'members_count': getattr(chat, 'members_count', None)
            }
        except Exception as e:
            print(f"Error getting chat info: {e}")
            return None
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.is_connected:
            await self.client.stop()
            self.is_connected = False
            print("[OK] Telegram နဲ့ disconnect လုပ်ပြီးပါပြီ။")
    
    def get_client(self):
        """Get the Pyrogram client instance"""
        return self.client
