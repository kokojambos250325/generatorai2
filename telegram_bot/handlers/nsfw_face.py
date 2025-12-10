"""
NSFW Face Handler

Handles NSFW face-consistent generation flow.
"""

import logging
import base64
import time
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import get_style_keyboard, get_examples_keyboard, get_main_menu_keyboard
from telegram_bot.utils.validators import validate_photo
from telegram_bot.utils.logger import get_bot_logger
from telegram_bot.utils.error_handler import handle_error, send_error_message
from telegram_bot.states import NSFWFaceState, set_user_state, clear_user_state

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()
api_client = BackendAPIClient()


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def start_nsfw_face(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start NSFW face generation flow"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Set state
    set_user_state(context, NSFWFaceState.WAITING_FACES.value)
    context.user_data['mode'] = 'nsfw_face'
    context.user_data['face_images'] = []
    
    # Create start text similar to competitor
    if lang == "ru":
        start_text = (
            f"🔞 **Отправьте мне 1-5 фотографий лица, с которым мы создадим искусство 😉**\n\n"
            f"Загрузите фото лица девушки и увидите её в горячих 18+ сценах, о которых вы всегда мечтали! "
            f"Создайте то, что казалось невозможным.\n\n"
            f"⚠️ Первое лицо — главное. Оно влияет сильнее других.\n\n"
            f"📖 [Как выбрать лицо](https://t.me/example)"
        )
    else:
        start_text = locale.get_text("nsfw_face.start", lang)
    
    if query:
        await query.edit_message_text(start_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(start_text, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "nsfw_face_started", mode="nsfw_face")


async def handle_face_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle face photo upload"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Check if user is in NSFW face mode
    if context.user_data.get('mode') != 'nsfw_face':
        return
    
    # Get photo
    photo = update.message.photo[-1]  # Get largest photo
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Validate photo
    is_valid, error_msg, metadata = validate_photo(
        bytes(photo_bytes),
        require_face=True
    )
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return
    
    # Add to face images
    if 'face_images' not in context.user_data:
        context.user_data['face_images'] = []
    
    face_images = context.user_data['face_images']
    
    if len(face_images) >= 5:
        await update.message.reply_text(
            locale.get_text("errors.max_photos_reached", lang, max=5)
        )
        return
    
    # Convert to base64
    face_base64 = base64.b64encode(photo_bytes).decode('utf-8')
    face_images.append(face_base64)
    
    count = len(face_images)
    await update.message.reply_text(
        locale.get_text("nsfw_face.photo_received", lang, count=count)
    )
    
    bot_logger.log_action(user_id, "nsfw_face_photo_uploaded", mode="nsfw_face", count=count)


async def handle_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'done' command after face photos"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'nsfw_face':
        return
    
    face_images = context.user_data.get('face_images', [])
    
    if len(face_images) == 0:
        await update.message.reply_text(
            locale.get_text("nsfw_face.start", lang)
        )
        return
    
    # Move to scene prompt state
    set_user_state(context, NSFWFaceState.WAITING_SCENE.value)
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            locale.get_text("nsfw_face.btn_guide", lang),
            callback_data="nsfw_show_guide"
        ),
        InlineKeyboardButton(
            locale.get_text("nsfw_face.btn_templates", lang),
            callback_data="nsfw_show_templates"
        )
    ]])
    
    await update.message.reply_text(
        locale.get_text("nsfw_face.prompt_request_with_help", lang, count=len(face_images)),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    bot_logger.log_action(user_id, "face_photos_done", mode="nsfw_face", count=len(face_images))


async def show_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show template prompts"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    templates_text = locale.get_text("nsfw_face.templates_title", lang)
    keyboard = get_examples_keyboard(locale, lang, mode="nsfw_face")
    
    await query.edit_message_text(templates_text, reply_markup=keyboard, parse_mode="Markdown")


async def handle_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, template_num: int):
    """Handle template prompt selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Get template prompt
    template_key = f"nsfw_face.template_{template_num}"
    scene_prompt = locale.get_text(template_key, lang)
    
    # Store prompt and proceed to style selection
    context.user_data['scene_prompt'] = scene_prompt
    set_user_state(context, NSFWFaceState.WAITING_STYLE.value)
    
    await query.edit_message_text(
        locale.get_text("nsfw_face.template_selected", lang),
        parse_mode="Markdown"
    )
    
    # Show style selection
    keyboard = get_style_keyboard(locale, lang, mode="nsfw_face")
    await query.message.reply_text(
        locale.get_text("free_generation.style_selection", lang),
        reply_markup=keyboard
    )
    
    bot_logger.log_action(user_id, "template_selected", mode="nsfw_face", template_num=template_num)


async def handle_scene_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scene prompt input"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'nsfw_face':
        return
    
    # Check state
    current_state = context.user_data.get('state')
    if current_state != NSFWFaceState.WAITING_SCENE.value:
        return
    
    scene_prompt = update.message.text.strip()
    
    # Validate prompt
    from telegram_bot.utils.validators import validate_prompt
    is_valid, error_msg = validate_prompt(scene_prompt, min_length=5)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return
    
    context.user_data['scene_prompt'] = scene_prompt
    set_user_state(context, NSFWFaceState.WAITING_STYLE.value)
    
    # Show style selection
    keyboard = get_style_keyboard(locale, lang, mode="nsfw_face")
    await update.message.reply_text(
        locale.get_text("free_generation.style_selection", lang),
        reply_markup=keyboard
    )
    
    bot_logger.log_action(user_id, "scene_prompt_received", mode="nsfw_face")


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """Handle style selection and start generation"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'nsfw_face':
        return
    
    face_images = context.user_data.get('face_images', [])
    scene_prompt = context.user_data.get('scene_prompt')
    
    if not face_images or not scene_prompt:
        await query.edit_message_text(
            locale.get_text("errors.generic", lang)
        )
        return
    
    # Set generating state
    set_user_state(context, NSFWFaceState.GENERATING.value)
    
    # Show generating message
    await query.edit_message_text(
        locale.get_text("nsfw_face.generating", lang),
        parse_mode="Markdown"
    )
    
    start_time = time.time()
    
    try:
        # Call API
        result = await api_client.generate_nsfw_face(
            face_images=face_images,
            scene_prompt=scene_prompt,
            style=style
        )
        
        generation_time = time.time() - start_time
        
        if result.get('status') == 'done' and result.get('image'):
            # Send result
            image_data = base64.b64decode(result['image'])
            await query.message.reply_photo(
                photo=image_data,
                caption=locale.get_text("nsfw_face.success", lang)
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="nsfw_face",
                prompt=scene_prompt,
                style=style,
                status="success",
                time_seconds=generation_time
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            await query.edit_message_text(
                locale.get_text("errors.processing_failed", lang, error=error_msg)
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="nsfw_face",
                prompt=scene_prompt,
                style=style,
                status="failed",
                time_seconds=generation_time,
                error=error_msg
            )
    
    except Exception as e:
        generation_time = time.time() - start_time
        await send_error_message(update, context, e, lang)
        
        bot_logger.log_generation(
            user_id=user_id,
            mode="nsfw_face",
            prompt=scene_prompt,
            style=style,
            status="failed",
            time_seconds=generation_time,
            error=str(e)
        )
    
    finally:
        clear_user_state(context)
        
        # Show main menu
        keyboard = get_main_menu_keyboard(locale, lang)
        await query.message.reply_text(
            locale.get_text("common.choose_mode", lang),
            reply_markup=keyboard
        )

