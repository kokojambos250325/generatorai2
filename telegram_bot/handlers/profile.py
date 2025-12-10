"""
User Profile Handler

Shows user statistics, history, settings, and limits.
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


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Get balance and statistics (simplified - in production would use database)
    balance = context.user_data.get('balance', 0)
    
    profile_text = f"👤 **{locale.get_text('profile.title', lang)}**\n\n"
    
    # Balance section
    profile_text += f"{locale.get_text('profile.balance', lang)}\n"
    profile_text += f"{locale.get_text('balance.current_balance', lang, amount=balance)}\n\n"
    
    # Statistics section
    profile_text += f"{locale.get_text('profile.statistics', lang)}\n"
    profile_text += f"• {locale.get_text('profile.total_generations', lang, count=0)}\n"
    profile_text += f"• {locale.get_text('profile.free_generations', lang, count=0)}\n"
    profile_text += f"• {locale.get_text('profile.nsfw_generations', lang, count=0)}\n"
    profile_text += f"• {locale.get_text('profile.clothes_removals', lang, count=0)}\n\n"
    
    # Settings section
    profile_text += f"{locale.get_text('profile.settings', lang)}\n"
    profile_text += f"• {locale.get_text('profile.language', lang, lang=lang.upper())}\n"
    
    keyboard = get_main_menu_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(profile_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(profile_text, reply_markup=keyboard, parse_mode="Markdown")

