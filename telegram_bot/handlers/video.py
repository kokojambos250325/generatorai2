"""
Video Animation Handler

Handles video animation from photos (coming soon feature).
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import get_main_menu_keyboard
from telegram_bot.utils.logger import get_bot_logger

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def start_video_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start video animation flow"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # For now, show coming soon message
    # In future, this will handle photo upload and video generation
    video_text = (
        f"🎬 **{locale.get_text('video_animation.title', lang)}**\n\n"
        f"{locale.get_text('video_animation.coming_soon', lang)}"
    )
    
    keyboard = get_main_menu_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(video_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(video_text, reply_markup=keyboard, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "video_animation_opened")

