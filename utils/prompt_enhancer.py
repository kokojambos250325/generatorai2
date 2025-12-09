"""
Prompt Enhancement for Free Generation Mode
Адаптирует пользовательские запросы в качественные промпты для SDXL
"""

STYLE_PRESETS = {
    "luxury": {
        "name": "Люкс",
        "prefix": "masterpiece, best quality, ultra-detailed, photorealistic, 8k uhd, professional photography, dramatic lighting, ",
        "suffix": ", highly detailed skin, perfect anatomy, depth of field, bokeh, luxury style",
        "negative": "low quality, worst quality, bad anatomy, deformed, distorted, blurry, jpeg artifacts, watermark"
    },
    "realism": {
        "name": "Реализм", 
        "prefix": "realistic photo, high quality, natural lighting, sharp focus, ",
        "suffix": ", detailed skin texture, realistic proportions, natural colors, film grain",
        "negative": "cartoon, anime, painting, drawing, low quality, blurry, distorted, bad anatomy"
    },
    "anime": {
        "name": "Аниме",
        "prefix": "anime style, high quality illustration, detailed, vibrant colors, ",
        "suffix": ", anime shading, expressive eyes, smooth skin, digital art",
        "negative": "realistic, photo, 3d render, low quality, blurry, bad anatomy, deformed"
    }
}

# Типичные элементы, которые нужно всегда добавлять если не указаны
DEFAULT_QUALITY_TAGS = [
    "high quality",
    "detailed", 
    "sharp focus"
]

# Автоматические улучшения для анатомии и качества
ANATOMY_ENHANCERS = {
    "face": "beautiful detailed face, expressive eyes, detailed lips",
    "body": "perfect anatomy, detailed skin, natural proportions",
    "hands": "detailed hands, five fingers",
    "overall": "realistic skin texture, natural pose"
}


def enhance_prompt(user_input: str, style: str = "realism") -> dict:
    """
    Улучшает пользовательский промпт, добавляя технические детали
    
    Args:
        user_input: Исходный запрос пользователя
        style: Стиль генерации (luxury/realism/anime)
        
    Returns:
        dict с полями: positive_prompt, negative_prompt, style_name
    """
    if style not in STYLE_PRESETS:
        style = "realism"
    
    preset = STYLE_PRESETS[style]
    
    # Очистка и нормализация ввода
    user_clean = user_input.strip()
    
    # Проверка на пустой промпт
    if not user_clean:
        user_clean = "beautiful woman, elegant pose, professional photo"
    
    # Формирование позитивного промпта
    positive_parts = [
        preset["prefix"],
        user_clean,
        preset["suffix"]
    ]
    
    # Добавляем улучшения анатомии если в запросе есть люди
    human_keywords = ["woman", "man", "girl", "guy", "person", "девушк", "парн", "женщин", "мужчин"]
    if any(kw in user_clean.lower() for kw in human_keywords):
        positive_parts.insert(2, ANATOMY_ENHANCERS["overall"])
    
    positive_prompt = ", ".join(positive_parts)
    
    # Негативный промпт
    negative_prompt = preset["negative"]
    
    return {
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "style_name": preset["name"]
    }


def translate_russian_to_tags(text: str) -> str:
    """
    Базовый перевод типичных русских фраз в английские теги
    Можно расширить словарь переводов
    """
    # Словарь распространённых переводов
    translations = {
        # Позы
        "стоя": "standing",
        "сидя": "sitting", 
        "лежа": "lying down",
        
        # Локации
        "на пляже": "at the beach, sandy beach, ocean background",
        "в комнате": "in bedroom, interior",
        "на улице": "outdoors, street",
        "в лесу": "in forest, trees, nature",
        
        # Одежда
        "голая": "nude, naked",
        "в платье": "wearing dress",
        "в купальнике": "wearing swimsuit, bikini",
        "в белье": "wearing lingerie",
        
        # Внешность
        "блондинка": "blonde hair",
        "брюнетка": "brunette, dark hair",
        "рыжая": "redhead, ginger hair",
        "стройная": "slim body, fit",
        "пышная": "curvy body, voluptuous",
        
        # Качество
        "красивая": "beautiful, attractive",
        "сексуальная": "sexy, seductive"
    }
    
    result = text
    for ru, en in translations.items():
        result = result.replace(ru, en)
    
    return result


def build_full_prompt(user_request: str, style: str = "realism", auto_translate: bool = True) -> dict:
    """
    Полная обработка запроса пользователя
    
    Args:
        user_request: Исходный текст от пользователя
        style: luxury/realism/anime
        auto_translate: Автоматически переводить русские фразы
        
    Returns:
        Готовый промпт для генерации
    """
    # Опционально переводим русские фразы
    if auto_translate:
        processed = translate_russian_to_tags(user_request)
    else:
        processed = user_request
    
    # Применяем стилевые улучшения
    result = enhance_prompt(processed, style)
    
    return result


# ===== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ =====

if __name__ == "__main__":
    # Пример 1: Простой запрос
    user_input_1 = "девушка на пляже"
    result_1 = build_full_prompt(user_input_1, style="realism")
    print("=== Пример 1: Реализм ===")
    print(f"Запрос: {user_input_1}")
    print(f"Positive: {result_1['positive_prompt']}")
    print(f"Negative: {result_1['negative_prompt']}\n")
    
    # Пример 2: Детальный запрос
    user_input_2 = "стройная блондинка в купальнике лежа на пляже, закат"
    result_2 = build_full_prompt(user_input_2, style="luxury")
    print("=== Пример 2: Люкс ===")
    print(f"Запрос: {user_input_2}")
    print(f"Positive: {result_2['positive_prompt']}")
    print(f"Negative: {result_2['negative_prompt']}\n")
    
    # Пример 3: Аниме стиль
    user_input_3 = "красивая девушка с рыжими волосами"
    result_3 = build_full_prompt(user_input_3, style="anime")
    print("=== Пример 3: Аниме ===")
    print(f"Запрос: {user_input_3}")
    print(f"Positive: {result_3['positive_prompt']}")
    print(f"Negative: {result_3['negative_prompt']}")
