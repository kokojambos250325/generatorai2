"""
Free Generation Handler

Conversation flow for text-to-image generation.

Flow:
1. User selects Free Generation
2. Bot asks for text prompt
3. User sends prompt
4. Bot asks for style
5. User selects style
6. Bot generates image
7. Bot shows result and returns to main menu
"""

import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import get_settings
from handlers import start

logger = logging.getLogger(__name__)
settings = get_settings()

# Track users in free generation flow
active_users = set()


def get_active_users():
    """Return set of users currently in free generation flow"""
    return active_users


async def start_free_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start free generation conversation.
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Add user to active users
    active_users.add(user_id)
    
    # Store state
    context.user_data['mode'] = 'free_generation'
    context.user_data['step'] = 'waiting_prompt'
    
    await query.edit_message_text(
        "🎨 **Free Generation**\n\n"
        "Send me a text description of the image you want to generate.\n\n"
        "Example: *a beautiful mountain landscape at sunset, photorealistic*\n\n"
        "Or use /start to return to main menu.",
        parse_mode="Markdown"
    )


async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text prompt from user.
    """
    user_id = update.effective_user.id
    
    # Check if user is in free generation flow
    if user_id not in active_users:
        return
    
    # Check step
    if context.user_data.get('step') != 'waiting_prompt':
        return
    
    # Get prompt
    prompt = update.message.text.strip()
    
    if not prompt or len(prompt) < 3:
        await update.message.reply_text(
            "❌ Prompt is too short. Please provide a more detailed description."
        )
        return
    
    # Store prompt
    context.user_data['prompt'] = prompt
    context.user_data['step'] = 'waiting_style'
    
    logger.info(f"User {user_id} provided prompt: {prompt[:50]}...")
    
    # Ask for style
    keyboard = [
        [InlineKeyboardButton("📸 Realism", callback_data="style_realism")],
        [InlineKeyboardButton("✨ Lux", callback_data="style_lux")],
        [InlineKeyboardButton("🎌 Anime", callback_data="style_anime")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="style_chatgpt")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Great! Now choose a style:",
        reply_markup=reply_markup
    )


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """
    Handle style selection and trigger generation.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Store style
    context.user_data['style'] = style
    
    logger.info(f"User {user_id} selected style: {style}")
    
    # Show generating message
    await query.edit_message_text(
        f"🎨 Generating image with **{style}** style...\n\n"
        "This may take 30-60 seconds. Please wait.",
        parse_mode="Markdown"
    )
    
    # Call backend API
    try:
        prompt = context.user_data['prompt']
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.backend_api_url}/generate",
                json={
                    "mode": "free",
                    "prompt": prompt,
                    "style": style,
                    "extra_params": {
                        "steps": 30,
                        "cfg_scale": 7.5,
                        "seed": -1
                    }
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result['status'] == 'done' and result['image']:
                # Send image
                import base64
                import io
                
                image_data = base64.b64decode(result['image'])
                
                await query.message.reply_photo(
                    photo=io.BytesIO(image_data),
                    caption=f"✅ Generated with **{style}** style!\n\nPrompt: _{prompt[:100]}_",
                    parse_mode="Markdown"
                )
                
                logger.info(f"Successfully generated image for user {user_id}")
            
            else:
                # Error
                error_msg = result.get('error', 'Unknown error')
                await query.message.reply_text(
                    f"❌ Generation failed: {error_msg}\n\nPlease try again."
                )
                logger.error(f"Generation failed for user {user_id}: {error_msg}")
    
    except httpx.TimeoutException:
        await query.message.reply_text(
            "❌ Generation timeout. The request took too long.\n\nPlease try again with a simpler prompt."
        )
        logger.error(f"Timeout for user {user_id}")
    
    except Exception as e:
        await query.message.reply_text(
            f"❌ An error occurred: {str(e)}\n\nPlease try again."
        )
        logger.error(f"Error for user {user_id}: {e}", exc_info=True)
    
    finally:
        # Clean up
        active_users.discard(user_id)
        context.user_data.clear()
        
        # Show main menu
        await start.show_main_menu(update, context)
