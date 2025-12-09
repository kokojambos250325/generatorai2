"""
Entry point for Telegram Bot
Run this file to start the Telegram bot
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_bot.bot import main

if __name__ == "__main__":
    print("=" * 60)
    print("AI Image Generation Telegram Bot")
    print("=" * 60)
    print("\nStarting bot...\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
