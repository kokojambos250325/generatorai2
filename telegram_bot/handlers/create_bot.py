"""
Create Bot Handler

Handles referral program and bot creation feature.
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


async def show_create_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show create bot menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # For now, show coming soon message
    # In future, this will handle bot creation and referral program
    create_bot_text = (
        f"🤖 **{locale.get_text('create_bot.title', lang)}**\n\n"
        f"{locale.get_text('create_bot.coming_soon', lang)}"
    )
    
    keyboard = get_main_menu_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(create_bot_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(create_bot_text, reply_markup=keyboard, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "create_bot_opened")

