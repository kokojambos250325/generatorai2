"""
Balance and Top-up Handler

Handles balance display and payment top-up functionality.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import get_topup_keyboard, get_main_menu_keyboard
from telegram_bot.utils.logger import get_bot_logger

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user balance"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Get balance from user_data (in production would use database)
    balance = context.user_data.get('balance', 0)
    
    balance_text = (
        f"💰 **{locale.get_text('profile.balance', lang)}**\n\n"
        f"{locale.get_text('balance.current_balance', lang, amount=balance)}\n\n"
        f"💡 Пополните баланс для использования функций бота."
    )
    
    keyboard = get_main_menu_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(balance_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(balance_text, reply_markup=keyboard, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "balance_viewed", balance=balance)


async def show_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top-up menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    topup_text = (
        f"💳 **{locale.get_text('balance.topup_title', lang)}**\n\n"
        f"{locale.get_text('balance.topup_info', lang)}\n\n"
        f"{locale.get_text('balance.topup_warning', lang)}\n\n"
        f"{locale.get_text('balance.topup_amounts', lang)}"
    )
    
    keyboard = get_topup_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(topup_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(topup_text, reply_markup=keyboard, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "topup_menu_opened")


async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    """Handle top-up amount selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # In production, this would integrate with payment gateway
    # For now, just show coming soon message
    await query.edit_message_text(
        f"💳 Пополнение на {amount} ₽\n\n"
        f"🚧 Интеграция с платежной системой в разработке.\n\n"
        f"В будущем здесь будет возможность пополнить баланс через СБП, карту или криптовалюту.",
        parse_mode="Markdown"
    )
    
    bot_logger.log_action(user_id, "topup_selected", amount=amount)

