"""
Help and Instructions Handler

Provides help menu with guides, examples, limitations, etc.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import get_help_menu_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    help_text = locale.get_text("help.title", lang)
    keyboard = get_help_menu_keyboard(locale, lang)
    
    if query:
        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(help_text, reply_markup=keyboard, parse_mode="Markdown")


async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    callback_data = query.data
    
    if callback_data == "help_generation_problems":
        text = locale.get_text("help.generation_problems_content", lang)
    
    elif callback_data == "help_payment_problems":
        text = locale.get_text("help.payment_problems_content", lang)
    
    elif callback_data == "help_tech_support":
        text = locale.get_text("help.tech_support_content", lang)
    
    elif callback_data == "help_prompt_guide":
        content = locale.get_text("help.prompt_guide_content", lang)
        title = locale.get_text("help.prompt_guide", lang)
        text = f"{title}\n\n{content}"
    
    elif callback_data == "help_examples":
        # Show examples from free_generation
        examples = []
        for i in range(1, 6):
            example = locale.get_text(f"free_generation.example_{i}", lang)
            examples.append(f"{i}. {example}")
        
        text = f"📋 **{locale.get_text('help.examples', lang)}**\n\n" + "\n\n".join(examples)
    
    elif callback_data == "help_style_guide":
        content = locale.get_text("help.style_guide_content", lang)
        title = locale.get_text("help.style_guide", lang)
        text = f"{title}\n\n{content}"
    
    elif callback_data == "help_limitations":
        content = locale.get_text("help.limitations_content", lang)
        title = locale.get_text("help.limitations", lang)
        text = f"{title}\n\n{content}"
    
    elif callback_data == "help_face_improvement":
        content = locale.get_text("help.face_improvement_content", lang)
        title = locale.get_text("help.face_improvement", lang)
        text = f"{title}\n\n{content}"
    
    elif callback_data == "help_prohibited":
        content = locale.get_text("help.prohibited_content", lang)
        title = locale.get_text("help.prohibited", lang)
        text = f"{title}\n\n{content}"
    
    else:
        await show_help_menu(update, context)
        return
    
    # Back button
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "< " + locale.get_text("buttons.back_to_menu", lang).replace("🔙 ", ""),
                callback_data="show_help"
            )
        ],
        [
            InlineKeyboardButton(
                "<< " + locale.get_text("main_menu.welcome", lang).split("\n")[0].replace("👋 ", "").replace("!", ""),
                callback_data="back_to_menu"
            )
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

