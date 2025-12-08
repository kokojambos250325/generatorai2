"""
Start Command and Main Menu Handler

Displays welcome message and main menu with 2 buttons for MVP modes.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    
    Displays welcome message and main menu.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started bot")
    
    # Welcome message
    welcome_text = (
        f"👋 Welcome, {user.first_name}!\n\n"
        "🎨 **AI Image Generation Bot**\n\n"
        "I can help you create amazing images using AI. Choose a mode below:\n\n"
        "🎨 **Free Generation** - Create images from text descriptions\n"
        "👕 **Remove Clothes** - Remove clothing from photos\n\n"
        "Select an option to get started:"
    )
    
    # Create keyboard with 2 buttons (MVP)
    keyboard = [
        [InlineKeyboardButton("🎨 Free Generation", callback_data="mode_free")],
        [InlineKeyboardButton("👕 Remove Clothes", callback_data="mode_clothes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button callbacks from main menu.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    logger.info(f"User {user_id} selected: {callback_data}")
    
    if callback_data == "mode_free":
        # Import here to avoid circular imports
        from handlers import free
        await free.start_free_generation(update, context)
    
    elif callback_data == "mode_clothes":
        # Import here to avoid circular imports
        from handlers import clothes
        await clothes.start_clothes_removal(update, context)
    
    else:
        await query.edit_message_text("❌ Unknown option. Please use /start to try again.")


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show main menu (called from other handlers to return to menu).
    """
    keyboard = [
        [InlineKeyboardButton("🎨 Free Generation", callback_data="mode_free")],
        [InlineKeyboardButton("👕 Remove Clothes", callback_data="mode_clothes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "Choose a mode:",
        reply_markup=reply_markup
    )
