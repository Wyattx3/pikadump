"""
Telegram Card Extractor - Main Application
Entry point for the card extraction script
"""
import asyncio
import signal
import sys
import os
from typing import List
from telegram_client import TelegramClient
from message_handler import MessageHandler
from data_manager import DataManager

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None


class CardExtractorApp:
    """Main application class"""
    
    def __init__(self):
        self.telegram_client = None
        self.message_handler = None
        self.data_manager = DataManager()
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n\n[!] Shutting down...")
        self.running = False
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.telegram_client:
            await self.telegram_client.disconnect()
        
        # Print final stats
        stats = self.data_manager.get_stats()
        print("\n" + "=" * 60)
        print("Final Statistics:")
        print(f"  Total Cards Found: {stats['total_cards']}")
        print(f"  Cards by Type: {stats['by_type']}")
        print(f"  Cards by Channel: {stats['by_channel']}")
        print("=" * 60)
        print("\n[OK] Application closed successfully.")
        sys.exit(0)
    
    def print_banner(self):
        """Print application banner"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║         Telegram Card Extractor                          ║
║         Real-time Card Monitoring System                  ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    async def select_chats(self):
        """Let user select channels/groups to monitor"""
        print("\n=== Channel/Group Selection ===\n")
        
        # Get available channels and groups
        chats = await self.telegram_client.get_channels_and_groups()
        
        if not chats:
            print("[X] Channels သို့မဟုတ် Groups မတွေ့ရှိပါဘူး။")
            return []
        
        # Display available chats
        print("Available Channels/Groups:\n")
        for i, chat in enumerate(chats, 1):
            chat_type = chat['type']
            username = f"@{chat['username']}" if chat['username'] else "N/A"
            print(f"  {i}. {chat['title']} ({chat_type}) - {username}")
        
        print("\n" + "-" * 60)
        print("Select channels/groups to monitor:")
        print("  - Enter numbers separated by commas (e.g., 1,2,3)")
        print("  - Enter 'all' to monitor all channels/groups")
        print("  - Press Enter to skip")
        
        selection = input("\nYour selection: ").strip().lower()
        
        selected_chats = []
        
        if selection == 'all':
            selected_chats = [chat['id'] for chat in chats]
            print(f"\n[OK] All {len(selected_chats)} channels/groups selected.")
        elif selection:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_chats = [chats[i]['id'] for i in indices if 0 <= i < len(chats)]
                
                if selected_chats:
                    selected_names = [chats[i]['title'] for i in indices if 0 <= i < len(chats)]
                    print(f"\n[OK] Selected {len(selected_chats)} channel(s)/group(s):")
                    for name in selected_names:
                        print(f"    - {name}")
                else:
                    print("\n[X] Invalid selection.")
            except ValueError:
                print("\n[X] Invalid input format.")
        
        return selected_chats
    
    async def process_history_option(self, chat_ids: List[int]):
        """Ask user if they want to process message history"""
        print("\n" + "-" * 60)
        print("Do you want to process existing message history?")
        print("  - Enter 'yes' to process all history")
        print("  - Enter number (e.g., 1000) to process last N messages")
        print("  - Press Enter to skip")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'yes':
            limit = None
        elif choice.isdigit():
            limit = int(choice)
        else:
            return
        
        print("\n[+] Processing message history...")
        for chat_id in chat_ids:
            await self.message_handler.process_history(chat_id, limit=limit)
    
    async def run(self):
        """Main application flow"""
        try:
            self.print_banner()
            
            # Initialize Telegram client
            print("\n[+] Initializing Telegram client...")
            self.telegram_client = TelegramClient()
            
            # Authenticate
            print("\n[+] Authenticating...")
            auth_success = await self.telegram_client.authenticate()
            
            if not auth_success:
                print("\n[X] Authentication failed. Exiting...")
                return
            
            # Connect
            await self.telegram_client.connect()
            
            # Select chats to monitor
            selected_chats = await self.select_chats()
            
            if not selected_chats:
                print("\n[X] No channels/groups selected. Exiting...")
                await self.telegram_client.disconnect()
                return
            
            # Initialize message handler
            self.message_handler = MessageHandler(
                self.telegram_client.get_client(),
                selected_chats
            )
            
            # Option to process history
            await self.process_history_option(selected_chats)
            
            # Start real-time monitoring
            if self.running:
                await self.message_handler.start_monitoring()
            
        except KeyboardInterrupt:
            print("\n\n[!] Interrupted by user.")
        except Exception as e:
            print(f"\n[X] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()


async def main():
    """Entry point"""
    app = CardExtractorApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[OK] Application closed.")
        sys.exit(0)
