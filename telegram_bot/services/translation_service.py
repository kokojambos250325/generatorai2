"""
Translation Service - Multi-language prompt translation to English

Uses M2M100 model for translating prompts from any supported language to English
before sending to image generation model.
"""

import logging
from typing import Optional
import torch

logger = logging.getLogger(__name__)

# Lazy loading to avoid import errors if transformers not installed
_translator = None
_tokenizer = None
_model_loaded = False

# Language code mapping: Telegram bot language -> M2M100 language code
LANGUAGE_MAPPING = {
    "en": "en",      # English (no translation needed)
    "ru": "ru",      # Russian
    "de": "de",      # German
    "tr": "tr",      # Turkish
    "es": "es",      # Spanish
    "fr": "fr",      # French
    "ar": "ar",      # Arabic
}


def initialize_translator(model_name: str = "facebook/m2m100_418M", device: str = "auto"):
    """
    Initialize the translation model.
    
    Args:
        model_name: Hugging Face model identifier
        device: Device to load model on ('cuda', 'cpu', or 'auto')
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _translator, _tokenizer, _model_loaded
    
    if _model_loaded:
        logger.info("Translation model already loaded")
        return True
    
    try:
        from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
        
        logger.info(f"Loading translation model: {model_name}")
        
        # Determine device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load model and tokenizer
        _tokenizer = M2M100Tokenizer.from_pretrained(model_name)
        _translator = M2M100ForConditionalGeneration.from_pretrained(model_name)
        _translator.to(device)
        _translator.eval()
        
        _model_loaded = True
        logger.info(f"✅ Translation model loaded successfully on {device}")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import transformers: {e}")
        logger.error("Install with: pip install transformers sentencepiece")
        return False
    except Exception as e:
        logger.error(f"Failed to load translation model: {e}")
        return False


def translate_to_english(text: str, source_lang: str = "auto") -> Optional[str]:
    """
    Translate text from source language to English.
    
    Args:
        text: Text to translate
        source_lang: Source language code (ru, de, tr, es, fr, ar) or 'auto'
    
    Returns:
        Translated text in English, or None if translation fails
    """
    global _translator, _tokenizer, _model_loaded
    
    # Skip translation for English
    if source_lang == "en":
        logger.debug("Text is already in English, skipping translation")
        return text
    
    # Check if model is loaded
    if not _model_loaded:
        logger.warning("Translation model not loaded, attempting to initialize...")
        if not initialize_translator():
            logger.error("Failed to initialize translator, returning original text")
            return text
    
    try:
        # Map language code
        m2m_lang = LANGUAGE_MAPPING.get(source_lang, source_lang)
        
        # Set source and target languages
        _tokenizer.src_lang = m2m_lang
        
        # Tokenize input
        encoded = _tokenizer(text, return_tensors="pt")
        
        # Move to same device as model
        device = next(_translator.parameters()).device
        encoded = {k: v.to(device) for k, v in encoded.items()}
        
        # Generate translation
        generated_tokens = _translator.generate(
            **encoded,
            forced_bos_token_id=_tokenizer.get_lang_id("en"),
            max_length=512,
            num_beams=5,
            early_stopping=True
        )
        
        # Decode translation
        translated = _tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        
        logger.info(f"Translated ({source_lang}→en): '{text[:50]}...' → '{translated[:50]}...'")
        return translated
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        logger.warning("Returning original text")
        return text


def translate_prompt(prompt: str, user_language: str = "en") -> str:
    """
    High-level function to translate user prompt to English.
    
    This is the main function to use in bot handlers.
    
    Args:
        prompt: User's prompt text
        user_language: User's language code from locale manager
    
    Returns:
        English prompt suitable for image generation model
    """
    # Skip if already English
    if user_language == "en":
        return prompt
    
    # Attempt translation
    translated = translate_to_english(prompt, user_language)
    
    # Return translated or original if translation failed
    return translated if translated else prompt


# Preload model on module import (optional)
def preload_model():
    """Preload translation model to reduce first-time latency"""
    logger.info("Preloading translation model...")
    initialize_translator()


if __name__ == "__main__":
    # Test translation
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Translation Service")
    print("=" * 60)
    
    # Initialize
    if initialize_translator():
        print("✅ Model loaded\n")
        
        # Test cases
        test_cases = [
            ("ru", "красивая девушка на пляже в купальнике"),
            ("de", "ein schönes Mädchen am Strand"),
            ("fr", "une belle femme en robe élégante"),
            ("es", "una mujer hermosa con vestido"),
            ("tr", "plajda güzel bir kız"),
        ]
        
        for lang, text in test_cases:
            result = translate_to_english(text, lang)
            print(f"{lang.upper()}: {text}")
            print(f"EN:  {result}\n")
    else:
        print("❌ Failed to load model")
