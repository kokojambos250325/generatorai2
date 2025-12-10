"""
Free Generation Handler

Complete conversation flow for text-to-image generation with examples, guides, face option.
"""

import logging
import base64
import time
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import (
    get_style_keyboard, get_face_choice_keyboard, get_examples_keyboard,
    get_result_actions_keyboard, get_main_menu_keyboard
)
from telegram_bot.utils.validators import validate_prompt, validate_photo
from telegram_bot.utils.logger import get_bot_logger
from telegram_bot.utils.error_handler import send_error_message
from telegram_bot.states import FreeGenerationState, set_user_state, clear_user_state

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()
api_client = BackendAPIClient()


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def start_free_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start free generation conversation"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Set state
    set_user_state(context, FreeGenerationState.WAITING_PROMPT.value)
    context.user_data['mode'] = 'free_generation'
    context.user_data['face_images'] = []
    
    # Show start message with guide and examples buttons - styled like competitor
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Create welcome text similar to competitor
    if lang == "ru":
        start_text = (
            f"🎨 **Здесь вы можете создать любой свой запрос.**\n\n"
            f"Просто опишите какую картинку создать, наша нейросеть все сделает в лучшем виде, даже при минимальном запросе. "
            f"Чем детальнее ваш запрос, тем более ожидаемый результат вы получите, нейросеть пока не умеет читать ваши мысли :)\n\n"
            f"• Нет идей? 💡\n"
            f"  Позы, локации и готовые генерации каждый день!\n\n"
            f"• Как лучше писать запрос?\n"
            f"  Инструкция и важные нюансы\n\n"
            f"• Примеры моделей\n"
            f"  Вы можете указать любое окружение, самую желанную фантазию, одежду, и параметры внешности. "
            f"Все не указанные детали будут созданы на усмотрение нейросети"
        )
    else:
        start_text = (
            f"🎨 **Here you can create any of your requests.**\n\n"
            f"Just describe what picture to create, our neural network will do everything in the best way, even with a minimal request. "
            f"The more detailed your request, the more expected result you will get, the neural network cannot read your thoughts yet :)\n\n"
            f"• No ideas? 💡\n"
            f"  Poses, locations and ready-made generations every day!\n\n"
            f"• How to write a request better?\n"
            f"  Instructions and important nuances\n\n"
            f"• Model examples\n"
            f"You can specify any environment, the most desired fantasy, clothing, and appearance parameters. "
            f"All unspecified details will be created at the discretion of the neural network"
        )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                locale.get_text("free_generation.btn_guide", lang),
                callback_data="show_prompt_guide"
            ),
            InlineKeyboardButton(
                locale.get_text("free_generation.btn_examples", lang),
                callback_data="show_examples"
            )
        ]
    ])
    
    if query:
        await query.edit_message_text(start_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(start_text, reply_markup=keyboard, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "free_generation_started", mode="free")


async def show_prompt_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show prompt writing guide with examples"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Build guide message with examples
    guide_text = (
        f"💡 **{locale.get_text('free_generation.guide_title', lang)}**\n\n"
        f"{locale.get_text('free_generation.guide_body', lang)}\n\n"
        f"**{locale.get_text('free_generation.examples_title', lang)}**\n\n"
        f"1️⃣ {locale.get_text('free_generation.example_1', lang)}\n\n"
        f"2️⃣ {locale.get_text('free_generation.example_2', lang)}\n\n"
        f"3️⃣ {locale.get_text('free_generation.example_3', lang)}\n\n"
        f"4️⃣ {locale.get_text('free_generation.example_4', lang)}\n\n"
        f"5️⃣ {locale.get_text('free_generation.example_5', lang)}"
    )
    
    # Back button
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            locale.get_text("buttons.back_to_menu", lang),
            callback_data="mode_free"
        )
    ]])
    
    await query.edit_message_text(guide_text, reply_markup=keyboard, parse_mode="Markdown")


async def show_examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show examples menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    examples_text = locale.get_text("free_generation.examples_title", lang)
    keyboard = get_examples_keyboard(locale, lang, mode="free")
    
    await query.edit_message_text(examples_text, reply_markup=keyboard, parse_mode="Markdown")


async def handle_example_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, example_num: int):
    """Handle example prompt selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Get example prompt
    example_key = f"free_generation.example_{example_num}"
    prompt = locale.get_text(example_key, lang)
    
    # Store prompt and proceed to face choice
    context.user_data['prompt'] = prompt
    set_user_state(context, FreeGenerationState.WAITING_FACE.value)
    
    await query.edit_message_text(
        locale.get_text("free_generation.example_selected", lang),
        parse_mode="Markdown"
    )
    
    # Ask about face
    keyboard = get_face_choice_keyboard(locale, lang)
    await query.message.reply_text(
        locale.get_text("free_generation.add_face_question", lang),
        reply_markup=keyboard
    )
    
    bot_logger.log_action(user_id, "example_selected", mode="free", example_num=example_num)


async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text prompt from user"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Check if user is in free generation mode
    if context.user_data.get('mode') != 'free_generation':
        return
    
    # Get prompt
    prompt = update.message.text.strip()
    
    # Validate prompt
    is_valid, error_msg = validate_prompt(prompt, min_length=3)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return
    
    # Store prompt
    context.user_data['prompt'] = prompt
    set_user_state(context, FreeGenerationState.WAITING_FACE.value)
    
    bot_logger.log_action(user_id, "prompt_received", mode="free", prompt_length=len(prompt))
    
    # Ask if user wants to add face
    keyboard = get_face_choice_keyboard(locale, lang)
    await update.message.reply_text(
        locale.get_text("free_generation.add_face_question", lang),
        reply_markup=keyboard
    )


async def handle_face_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's choice about adding face"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    choice = query.data
    
    if choice == "face_yes":
        # User wants to add face
        set_user_state(context, FreeGenerationState.WAITING_FACE.value)
        context.user_data['face_images'] = []
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                locale.get_text("free_generation.btn_face_done", lang),
                callback_data="face_done"
            )
        ]])
        
        await query.edit_message_text(
            locale.get_text("free_generation.face_upload_request", lang),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif choice == "face_no":
        # User doesn't want face - proceed to style selection
        set_user_state(context, FreeGenerationState.WAITING_STYLE.value)
        await show_style_selection(update, context)


async def handle_face_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle face photo upload"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Check if user is in face photo upload step
    if context.user_data.get('mode') != 'free_generation':
        return
    
    # Get photo
    photo = update.message.photo[-1]  # Get highest resolution
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
    face_images = context.user_data.get('face_images', [])
    
    if len(face_images) >= 5:
        await update.message.reply_text(
            locale.get_text("errors.max_photos_reached", lang, max=5)
        )
        return
    
    # Convert to base64
    face_base64 = base64.b64encode(photo_bytes).decode('utf-8')
    face_images.append(face_base64)
    context.user_data['face_images'] = face_images
    
    await update.message.reply_text(
        locale.get_text("free_generation.face_photo_received", lang, count=len(face_images))
    )
    
    bot_logger.log_action(user_id, "face_photo_uploaded", mode="free", count=len(face_images))


async def handle_face_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'done' with face photos - proceed to style selection"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    face_images = context.user_data.get('face_images', [])
    
    if len(face_images) == 0:
        # No face photos - proceed without face
        if query:
            await query.edit_message_text(
                locale.get_text("free_generation.add_face_question", lang)
            )
        return
    
    # Proceed to style selection
    set_user_state(context, FreeGenerationState.WAITING_STYLE.value)
    await show_style_selection(update, context)


async def show_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show style selection menu"""
    locale = get_locale(context)
    user_id = update.effective_user.id
    lang = locale.get_user_language(user_id)
    
    keyboard = get_style_keyboard(locale, lang, mode="free")
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            locale.get_text("free_generation.style_selection", lang),
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            locale.get_text("free_generation.style_selection", lang),
            reply_markup=keyboard
        )


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """Handle style selection and start generation"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'free_generation':
        return
    
    prompt = context.user_data.get('prompt')
    face_images = context.user_data.get('face_images', [])
    
    if not prompt:
        await query.edit_message_text(
            locale.get_text("errors.no_prompt", lang)
        )
        return
    
    # Validate style
    from telegram_bot.utils.validators import is_valid_style
    if not is_valid_style(style, mode="free"):
        await query.edit_message_text(
            locale.get_text("errors.invalid_style", lang)
        )
        return
    
    # Set generating state
    set_user_state(context, FreeGenerationState.GENERATING.value)
    
    # Show generating message
    await query.edit_message_text(
        locale.get_text("free_generation.generating", lang, style=style),
        parse_mode="Markdown"
    )
    
    start_time = time.time()
    
    try:
        # Call API
        result = await api_client.generate_free(
            prompt=prompt,
            style=style,
            face_images=face_images if face_images else None,
            add_face=len(face_images) > 0
        )
        
        generation_time = time.time() - start_time
        
        if result.get('status') == 'done' and result.get('image'):
            # Send result
            image_data = base64.b64decode(result['image'])
            caption = locale.get_text("free_generation.success", lang, style=style, prompt=prompt[:100])
            
            if face_images:
                caption += f"\n\n👤 Face embedding: {len(face_images)} reference(s)"
            
            await query.message.reply_photo(
                photo=image_data,
                caption=caption,
                parse_mode="Markdown"
            )
            
            # Show result actions
            keyboard = get_result_actions_keyboard(locale, lang, mode="free")
            await query.message.reply_text(
                locale.get_text("common.choose_mode", lang),
                reply_markup=keyboard
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="free",
                prompt=prompt,
                style=style,
                status="success",
                time_seconds=generation_time,
                has_face=len(face_images) > 0
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            await query.edit_message_text(
                locale.get_text("errors.processing_failed", lang, error=error_msg)
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="free",
                prompt=prompt,
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
            mode="free",
            prompt=prompt,
            style=style,
            status="failed",
            time_seconds=generation_time,
            error=str(e)
        )
    
    finally:
        clear_user_state(context)
