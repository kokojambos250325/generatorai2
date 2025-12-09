"""
Telegram Bot Handlers
"""
from telegram_bot.handlers.free import handle_free_generation
from telegram_bot.handlers.face_swap import handle_face_swap
from telegram_bot.handlers.clothes_removal import handle_clothes_removal
from telegram_bot.handlers.face_consistent import handle_face_consistent
from telegram_bot.handlers.status import handle_status_check

__all__ = [
    "handle_free_generation",
    "handle_face_swap",
    "handle_clothes_removal",
    "handle_face_consistent",
    "handle_status_check"
]
