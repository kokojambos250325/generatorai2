"""
Reusable Keyboards for Telegram Bot

Provides keyboard builders for menus, style selection, actions, etc.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot.utils.locale import LocaleManager


def get_main_menu_keyboard(locale_manager: LocaleManager, lang: str) -> InlineKeyboardMarkup:
    """Get main menu keyboard - styled like competitor but unique"""
    keyboard = [
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_clothes", lang),
            callback_data="mode_clothes"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_video", lang),
            callback_data="mode_video"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_free_face", lang),
            callback_data="mode_free_face_menu"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_nsfw_face", lang),
            callback_data="mode_nsfw_face"
        )],
        [
            InlineKeyboardButton(
                locale_manager.get_text("main_menu.btn_balance", lang),
                callback_data="show_balance"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("main_menu.btn_topup", lang),
                callback_data="show_topup"
            )
        ],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_help", lang),
            callback_data="show_help"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_create_bot", lang),
            callback_data="show_create_bot"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_style_keyboard(
    locale_manager: LocaleManager,
    lang: str,
    mode: str = "free"
) -> InlineKeyboardMarkup:
    """
    Get style selection keyboard
    
    Args:
        locale_manager: Locale manager
        lang: Language code
        mode: Generation mode (free, nsfw_face, clothes_removal)
    """
    if mode == "free":
        # Free generation styles
        styles = [
            ("noir", "main_menu.style_noir"),
            ("super_realism", "main_menu.style_super_realism"),
            ("anime", "main_menu.style_anime"),
            ("realism", "main_menu.style_realism"),
            ("lux", "main_menu.style_lux"),
            ("chatgpt", "main_menu.style_chatgpt")
        ]
        prefix = "style_"
    elif mode == "nsfw_face":
        # NSFW face styles
        styles = [
            ("realism", "main_menu.style_realism"),
            ("lux", "main_menu.style_lux"),
            ("anime", "main_menu.style_anime")
        ]
        prefix = "nsfw_style_"
    else:  # clothes_removal
        # Clothes removal styles
        styles = [
            ("realism", "main_menu.style_realism"),
            ("lux", "main_menu.style_lux"),
            ("anime", "main_menu.style_anime")
        ]
        prefix = "clothes_style_"
    
    keyboard = []
    for style_code, text_key in styles:
        keyboard.append([InlineKeyboardButton(
            locale_manager.get_text(text_key, lang),
            callback_data=f"{prefix}{style_code}"
        )])
    
    # Back button
    keyboard.append([InlineKeyboardButton(
        locale_manager.get_text("buttons.back_to_menu", lang),
        callback_data="back_to_menu"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(locale_manager: LocaleManager, current_lang: str) -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    keyboard = []
    for lang_code, lang_name in locale_manager.get_language_options().items():
        # Add checkmark for current language
        display_name = lang_name
        if lang_code == current_lang:
            display_name = f"✅ {display_name}"
        
        keyboard.append([InlineKeyboardButton(
            display_name,
            callback_data=f"lang_{lang_code}"
        )])
    
    # Back button
    keyboard.append([InlineKeyboardButton(
        locale_manager.get_text("buttons.back_to_menu", current_lang),
        callback_data="back_to_menu"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_result_actions_keyboard(
    locale_manager: LocaleManager,
    lang: str,
    mode: str
) -> InlineKeyboardMarkup:
    """
    Get keyboard with actions for generated result
    
    Args:
        locale_manager: Locale manager
        lang: Language code
        mode: Generation mode
    """
    keyboard = [
        [
            InlineKeyboardButton(
                locale_manager.get_text("result_actions.regenerate", lang),
                callback_data=f"regenerate_{mode}"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("result_actions.improve_quality", lang),
                callback_data=f"improve_{mode}"
            )
        ],
        [
            InlineKeyboardButton(
                locale_manager.get_text("result_actions.change_style", lang),
                callback_data=f"change_style_{mode}"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("result_actions.download", lang),
                callback_data=f"download_{mode}"
            )
        ],
        [InlineKeyboardButton(
            locale_manager.get_text("buttons.back_to_menu", lang),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_help_menu_keyboard(
    locale_manager: LocaleManager,
    lang: str
) -> InlineKeyboardMarkup:
    """Get help menu keyboard - styled like competitor"""
    keyboard = [
        [InlineKeyboardButton(
            locale_manager.get_text("help.generation_problems", lang),
            callback_data="help_generation_problems"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("help.payment_problems", lang),
            callback_data="help_payment_problems"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("help.tech_support", lang),
            callback_data="help_tech_support"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("buttons.back_to_menu", lang),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_topup_keyboard(
    locale_manager: LocaleManager,
    lang: str
) -> InlineKeyboardMarkup:
    """Get top-up amount selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_300", lang),
                callback_data="topup_300"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_500", lang),
                callback_data="topup_500"
            )
        ],
        [
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_1000", lang),
                callback_data="topup_1000"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_2000", lang),
                callback_data="topup_2000"
            )
        ],
        [
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_3000", lang),
                callback_data="topup_3000"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("balance.amount_5000", lang),
                callback_data="topup_5000"
            )
        ],
        [InlineKeyboardButton(
            locale_manager.get_text("buttons.back_to_menu", lang),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_free_face_menu_keyboard(
    locale_manager: LocaleManager,
    lang: str
) -> InlineKeyboardMarkup:
    """Get menu for free generation and face swap"""
    keyboard = [
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_free", lang),
            callback_data="mode_free"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("main_menu.btn_face_swap", lang),
            callback_data="mode_face_swap"
        )],
        [InlineKeyboardButton(
            locale_manager.get_text("buttons.back_to_menu", lang),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_face_choice_keyboard(
    locale_manager: LocaleManager,
    lang: str
) -> InlineKeyboardMarkup:
    """Get keyboard for face addition choice"""
    keyboard = [
        [
            InlineKeyboardButton(
                locale_manager.get_text("free_generation.btn_face_yes", lang),
                callback_data="face_yes"
            ),
            InlineKeyboardButton(
                locale_manager.get_text("free_generation.btn_face_no", lang),
                callback_data="face_no"
            )
        ],
        [InlineKeyboardButton(
            locale_manager.get_text("buttons.back_to_menu", lang),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_examples_keyboard(
    locale_manager: LocaleManager,
    lang: str,
    mode: str = "free"
) -> InlineKeyboardMarkup:
    """
    Get keyboard with example prompts
    
    Args:
        locale_manager: Locale manager
        lang: Language code
        mode: Generation mode (free or nsfw_face)
    """
    keyboard = []
    
    if mode == "free":
        # Free generation examples
        for i in range(1, 6):
            keyboard.append([InlineKeyboardButton(
                locale_manager.get_text(f"free_generation.btn_use_example", lang, num=i),
                callback_data=f"example_free_{i}"
            )])
    else:  # nsfw_face
        # NSFW face templates
        for i in range(1, 6):
            keyboard.append([InlineKeyboardButton(
                locale_manager.get_text(f"nsfw_face.btn_use_template", lang, num=i),
                callback_data=f"template_nsfw_{i}"
            )])
    
    # Back button
    keyboard.append([InlineKeyboardButton(
        locale_manager.get_text("buttons.back_to_menu", lang),
        callback_data="back_to_menu"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(
    locale_manager: LocaleManager,
    lang: str,
    confirm_callback: str,
    cancel_callback: str = "back_to_menu"
) -> InlineKeyboardMarkup:
    """Get confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                locale_manager.get_text("buttons.confirm", lang),
                callback_data=confirm_callback
            ),
            InlineKeyboardButton(
                locale_manager.get_text("buttons.cancel", lang),
                callback_data=cancel_callback
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

