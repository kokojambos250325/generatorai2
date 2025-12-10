"""
FSM States for Telegram Bot

Defines conversation states for different generation modes.
"""

from enum import Enum


class FreeGenerationState(Enum):
    """States for free generation flow"""
    WAITING_PROMPT = "free_waiting_prompt"
    WAITING_FACE = "free_waiting_face"
    WAITING_STYLE = "free_waiting_style"
    GENERATING = "free_generating"


class NSFWFaceState(Enum):
    """States for NSFW face generation flow"""
    WAITING_FACES = "nsfw_waiting_faces"
    WAITING_SCENE = "nsfw_waiting_scene"
    WAITING_STYLE = "nsfw_waiting_style"
    GENERATING = "nsfw_generating"


class ClothesRemovalState(Enum):
    """States for clothes removal flow"""
    WAITING_PHOTO = "clothes_waiting_photo"
    WAITING_CONFIRM = "clothes_waiting_confirm"
    WAITING_STYLE = "clothes_waiting_style"
    GENERATING = "clothes_generating"


def get_user_state(context) -> str:
    """Get current user state from context"""
    return context.user_data.get('state', None)


def set_user_state(context, state: str):
    """Set user state in context"""
    context.user_data['state'] = state


def clear_user_state(context):
    """Clear user state from context"""
    context.user_data.pop('state', None)
    context.user_data.pop('mode', None)
    context.user_data.pop('step', None)


def is_in_state(context, state: str) -> bool:
    """Check if user is in specific state"""
    return get_user_state(context) == state


def is_in_mode(context, mode: str) -> bool:
    """Check if user is in specific mode"""
    return context.user_data.get('mode') == mode

