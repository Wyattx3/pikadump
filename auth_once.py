"""
One-time authentication script
Run this first to create session, then use auto_gen_drop.py
"""
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER

async def main():
    print("=" * 50)
    print("   Telegram Authentication")
    print("=" * 50)
    
    app = Client(
        SESSION_NAME,
        api_id=int(API_ID),
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER
    )
    
    await app.start()
    me = await app.get_me()
    print(f"\n[OK] Logged in as: {me.first_name} (@{me.username})")
    print(f"[OK] Session saved to: {SESSION_NAME}.session")
    print("\nYou can now run: python auto_gen_drop.py")
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
