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
import base64
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import get_settings
from handlers import start

logger = logging.getLogger(__name__)
settings = get_settings()

# Track users in free generation flow
active_users = set()


def get_locale(context: ContextTypes.DEFAULT_TYPE):
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


def get_active_users():
    """Return set of users currently in free generation flow"""
    return active_users


async def start_free_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start free generation conversation.
    """
    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Add user to active users
    active_users.add(user_id)
    
    # Store state
    context.user_data['mode'] = 'free_generation'
    context.user_data['step'] = 'waiting_prompt'
    context.user_data['face_images'] = []  # Initialize empty face images list
    
    # Create guide button
    keyboard = [
        [InlineKeyboardButton(
            get_locale(context).get_text("free_generation.btn_guide", lang),
            callback_data="show_prompt_guide"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        get_locale(context).get_text("free_generation.start", lang),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_prompt_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show prompt writing guide with examples.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Build guide message with examples
    guide_text = (
        f"📝 **{get_locale(context).get_text('free_generation.guide_title', lang)}**\n\n"
        f"{get_locale(context).get_text('free_generation.guide_body', lang)}\n\n"
        f"**{get_locale(context).get_text('free_generation.examples_title', lang)}**\n\n"
        f"1️⃣ {get_locale(context).get_text('free_generation.example_1', lang)}\n\n"
        f"2️⃣ {get_locale(context).get_text('free_generation.example_2', lang)}\n\n"
        f"3️⃣ {get_locale(context).get_text('free_generation.example_3', lang)}\n\n"
        f"4️⃣ {get_locale(context).get_text('free_generation.example_4', lang)}\n\n"
        f"5️⃣ {get_locale(context).get_text('free_generation.example_5', lang)}\n\n"
        f"💡 {get_locale(context).get_text('free_generation.guide_tip', lang)}"
    )
    
    # Create back button
    keyboard = [
        [InlineKeyboardButton(
            get_locale(context).get_text("common.back", lang),
            callback_data="mode_free"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        guide_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text prompt from user.
    """
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
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
            get_locale(context).get_text("errors.prompt_too_short", lang)
        )
        return
    
    # Store prompt
    context.user_data['prompt'] = prompt
    context.user_data['step'] = 'waiting_face_choice'
    
    logger.info(f"User {user_id} provided prompt: {prompt[:50]}...")
    
    # Ask if user wants to add face
    keyboard = [
        [InlineKeyboardButton(
            get_locale(context).get_text("free_generation.btn_face_yes", lang),
            callback_data="face_yes"
        )],
        [InlineKeyboardButton(
            get_locale(context).get_text("free_generation.btn_face_no", lang),
            callback_data="face_no"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_locale(context).get_text("free_generation.add_face_question", lang),
        reply_markup=reply_markup
    )


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """
    Handle style selection and trigger generation.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Store style
    context.user_data['style'] = style
    
    logger.info(f"User {user_id} selected style: {style}")
    
    # Show generating message
    await query.edit_message_text(
        get_locale(context).get_text("free_generation.generating", lang, style=style),
        parse_mode="Markdown"
    )
    
    # Call backend API
    try:
        prompt = context.user_data['prompt']
        face_images = context.user_data.get('face_images', [])
        add_face = len(face_images) > 0
        
        request_data = {
            "mode": "free",
            "prompt": prompt,
            "style": style,
            "add_face": add_face,
            "extra_params": {
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            }
        }
        
        # Add face images if provided
        if add_face:
            request_data["face_images"] = face_images
            request_data["face_strength"] = 0.75
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.backend_api_url}/generate",
                json=request_data
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result['status'] == 'done' and result['image']:
                # Send image
                import base64
                import io
                
                image_data = base64.b64decode(result['image'])
                
                caption = get_locale(context).get_text(
                    "free_generation.success",
                    lang,
                    style=style,
                    prompt=prompt[:100]
                )
                
                if add_face:
                    caption += f"\n\n👤 Face embedding: {len(face_images)} reference(s)"
                
                await query.message.reply_photo(
                    photo=io.BytesIO(image_data),
                    caption=caption,
                    parse_mode="Markdown"
                )
                
                logger.info(f"Successfully generated image for user {user_id} (faces={len(face_images)})")
            
            else:
                # Error
                error_msg = result.get('error', 'Unknown error')
                await query.message.reply_text(
                    get_locale(context).get_text("errors.generation_failed", lang, error=error_msg)
                )
                logger.error(f"Generation failed for user {user_id}: {error_msg}")
    
    except httpx.TimeoutException:
        await query.message.reply_text(
            get_locale(context).get_text("errors.timeout", lang)
        )
        logger.error(f"Timeout for user {user_id}")
    
    except Exception as e:
        await query.message.reply_text(
            get_locale(context).get_text("errors.generic", lang, error=str(e))
        )
        logger.error(f"Error for user {user_id}: {e}", exc_info=True)
    
    finally:
        # Clean up
        active_users.discard(user_id)
        context.user_data.clear()
        
        # Show main menu
        await start.show_main_menu(update, context)


async def handle_face_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user's choice about adding face.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    choice = query.data
    
    if choice == "face_yes":
        # User wants to add face
        context.user_data['step'] = 'waiting_face_photos'
        
        await query.edit_message_text(
            get_locale(context).get_text("free_generation.face_upload_request", lang),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    get_locale(context).get_text("free_generation.btn_face_done", lang),
                    callback_data="face_done"
                )]
            ])
        )
    
    elif choice == "face_no":
        # User doesn't want face - proceed to style selection
        context.user_data['step'] = 'waiting_style'
        
        await show_style_menu(query, context, lang)


async def handle_face_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle face photo upload.
    """
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Check if user is in face photo upload step
    if context.user_data.get('step') != 'waiting_face_photos':
        return
    
    # Get photo
    photo = update.message.photo[-1]  # Get highest resolution
    
    # Download photo as base64
    try:
        import base64
        import io
        
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()
        base64_image = base64.b64encode(bytes(file_bytes)).decode('utf-8')
        
        # Store photo
        face_images = context.user_data.get('face_images', [])
        
        if len(face_images) >= 5:
            await update.message.reply_text(
                get_locale(context).get_text("free_generation.face_photos_max", lang)
            )
            return
        
        face_images.append(base64_image)
        context.user_data['face_images'] = face_images
        
        await update.message.reply_text(
            get_locale(context).get_text(
                "free_generation.face_photo_received",
                lang,
                count=len(face_images)
            )
        )
        
        logger.info(f"User {user_id} uploaded face photo {len(face_images)}/5")
    
    except Exception as e:
        await update.message.reply_text(
            get_locale(context).get_text("errors.photo_processing", lang, error=str(e))
        )
        logger.error(f"Failed to process face photo for user {user_id}: {e}")


async def handle_face_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle 'done' with face photos - proceed to style selection.
    """
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    face_images = context.user_data.get('face_images', [])
    
    if len(face_images) == 0:
        message = "⚠️ No face photos received. Proceeding without face embedding."
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
    
    # Proceed to style selection
    context.user_data['step'] = 'waiting_style'
    
    if query:
        await query.answer()
        await show_style_menu(query, context, lang)
    else:
        # Text command 'done'
        await update.message.reply_text(
            f"✅ Got {len(face_images)} face photo(s)! Now choose style:",
            reply_markup=get_style_keyboard(lang)
        )


async def show_style_menu(query, context, lang):
    """
    Show style selection menu.
    """
    keyboard = [
        [InlineKeyboardButton(
            "📸 Realism",
            callback_data="style_realism"
        )],
        [InlineKeyboardButton(
            "✨ Lux",
            callback_data="style_lux"
        )],
        [InlineKeyboardButton(
            "🎌 Anime",
            callback_data="style_anime"
        )],
        [InlineKeyboardButton(
            "🕶 Noir",
            callback_data="style_noir"
        )],
        [InlineKeyboardButton(
            "📸 Super Realism",
            callback_data="style_super_realism"
        )],
        [InlineKeyboardButton(
            "🤖 ChatGPT",
            callback_data="style_chatgpt"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        get_locale(context).get_text("free_generation.choose_style", lang),
        reply_markup=reply_markup
    )


def get_style_keyboard(lang):
    """
    Get style selection keyboard.
    """
    keyboard = [
        [InlineKeyboardButton(
            "📸 Realism",
            callback_data="style_realism"
        )],
        [InlineKeyboardButton(
            "✨ Lux",
            callback_data="style_lux"
        )],
        [InlineKeyboardButton(
            "🏌 Anime",
            callback_data="style_anime"
        )],
        [InlineKeyboardButton(
            "🕶 Noir",
            callback_data="style_noir"
        )],
        [InlineKeyboardButton(
            "📸 Super Realism",
            callback_data="style_super_realism"
        )],
        [InlineKeyboardButton(
            "🤖 ChatGPT",
            callback_data="style_chatgpt"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)
