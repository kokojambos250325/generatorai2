"""
Locale Manager для многоязычной поддержки

Управляет загрузкой, кэшированием и получением локализованных текстовых строк
для Telegram бота на 7 поддерживаемых языках.

Поддерживаемые языки:
- English (en) - Основной
- Russian (ru) - Основной  
- German (de)
- Turkish (tr)
- Spanish (es)
- French (fr)
- Arabic (ar)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class LocaleManager:
    """Управляет локализацией для многоязычной поддержки"""
    
    SUPPORTED_LANGUAGES = {
        "en": "🇬🇧 English",
        "ru": "🇷🇺 Русский",
        "de": "🇩🇪 Deutsch",
        "tr": "🇹🇷 Türkçe",
        "es": "🇪🇸 Español",
        "fr": "🇫🇷 Français",
        "ar": "🇦🇪 العربية"
    }
    
    DEFAULT_LANGUAGE = "en"
    
    def __init__(self, locales_dir: str = None, user_prefs_file: str = None):
        """
        Инициализация locale manager.
        
        Args:
            locales_dir: Путь к директории с JSON файлами локализации
            user_prefs_file: Путь к JSON файлу с языковыми предпочтениями пользователей
        """
        # Установка путей по умолчанию относительно директории telegram_bot
        if locales_dir is None:
            base_dir = Path(__file__).parent.parent
            locales_dir = base_dir / "locales"
        else:
            locales_dir = Path(locales_dir)
            
        if user_prefs_file is None:
            base_dir = Path(__file__).parent.parent
            user_prefs_file = base_dir / "data" / "user_languages.json"
        else:
            user_prefs_file = Path(user_prefs_file)
        
        self.locales_dir = locales_dir
        self.user_prefs_file = user_prefs_file
        self._locales: Dict[str, Dict[str, Any]] = {}
        self._user_preferences: Dict[str, str] = {}
        
        # Загрузка всех locale файлов
        self._load_locales()
        
        # Загрузка пользовательских предпочтений
        self._load_user_preferences()
    
    def _load_locales(self):
        """Загрузка всех JSON файлов локализации в память"""
        if not self.locales_dir.exists():
            logger.warning(f"Директория локализации не найдена: {self.locales_dir}")
            logger.info("Создание директории локализации...")
            self.locales_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            locale_file = self.locales_dir / f"{lang_code}.json"
            
            if not locale_file.exists():
                logger.warning(f"Файл локализации не найден для {lang_code}: {locale_file}")
                continue
            
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self._locales[lang_code] = json.load(f)
                logger.info(f"Загружена локаль: {lang_code} ({len(self._locales[lang_code])} ключей)")
            except Exception as e:
                logger.error(f"Не удалось загрузить локаль {lang_code}: {e}")
    
    def _load_user_preferences(self):
        """Загрузка языковых предпочтений пользователей из файла"""
        if not self.user_prefs_file.exists():
            logger.info(f"Файл предпочтений пользователей не найден: {self.user_prefs_file}")
            # Создание родительской директории если нужно
            self.user_prefs_file.parent.mkdir(parents=True, exist_ok=True)
            # Создание пустого файла предпочтений
            self._save_user_preferences()
            return
        
        try:
            with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                self._user_preferences = json.load(f)
            logger.info(f"Загружено {len(self._user_preferences)} языковых предпочтений пользователей")
        except Exception as e:
            logger.error(f"Не удалось загрузить предпочтения пользователей: {e}")
            self._user_preferences = {}
    
    def _save_user_preferences(self):
        """Сохранение языковых предпочтений пользователей в файл"""
        try:
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_preferences, f, ensure_ascii=False, indent=2)
            logger.debug(f"Сохранены предпочтения: {len(self._user_preferences)} пользователей")
        except Exception as e:
            logger.error(f"Не удалось сохранить предпочтения пользователей: {e}")
    
    def get_text(self, key: str, lang: str = None, **kwargs) -> str:
        """
        Получение локализованного текста по ключу.
        
        Args:
            key: Путь к ключу через точку (например, "main_menu.welcome")
            lang: Код языка (если None, используется язык по умолчанию)
            **kwargs: Аргументы для форматирования строки
        
        Returns:
            Локализованный текст с замененными плейсхолдерами
        """
        # Использование языка по умолчанию если не указан
        if lang is None:
            lang = self.DEFAULT_LANGUAGE
        
        # Валидация языка
        if lang not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Неподдерживаемый язык '{lang}', fallback на {self.DEFAULT_LANGUAGE}")
            lang = self.DEFAULT_LANGUAGE
        
        # Получение словаря локализации
        locale = self._locales.get(lang)
        if locale is None:
            logger.warning(f"Локаль не загружена для '{lang}', fallback на {self.DEFAULT_LANGUAGE}")
            locale = self._locales.get(self.DEFAULT_LANGUAGE, {})
        
        # Навигация по вложенным ключам (поддержка точечной нотации типа "main_menu.welcome")
        value = locale
        for key_part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(key_part)
            else:
                value = None
                break
        
        # Fallback на английский если ключ не найден
        if value is None:
            if lang != self.DEFAULT_LANGUAGE:
                logger.warning(f"Ключ '{key}' не найден в {lang}, пробую {self.DEFAULT_LANGUAGE}")
                return self.get_text(key, self.DEFAULT_LANGUAGE, **kwargs)
            else:
                logger.error(f"Ключ '{key}' не найден ни в одной локали")
                return f"[{key}]"
        
        # Обработка строкового значения
        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Отсутствует аргумент форматирования для '{key}': {e}")
                return value
        
        # Если значение не строка (например, вложенный dict), возвращаем ключ
        logger.warning(f"Ключ '{key}' не указывает на строковое значение")
        return f"[{key}]"
    
    def get_user_language(self, user_id: int) -> str:
        """
        Получение предпочитаемого языка пользователя.
        
        Args:
            user_id: Telegram ID пользователя
        
        Returns:
            Код языка (например, "en", "ru")
        """
        user_id_str = str(user_id)
        return self._user_preferences.get(user_id_str, self.DEFAULT_LANGUAGE)
    
    def set_user_language(self, user_id: int, lang: str) -> bool:
        """
        Установка предпочитаемого языка пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            lang: Код языка
        
        Returns:
            True если успешно, False если язык не поддерживается
        """
        if lang not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Попытка установить неподдерживаемый язык: {lang}")
            return False
        
        user_id_str = str(user_id)
        self._user_preferences[user_id_str] = lang
        self._save_user_preferences()
        
        logger.info(f"Пользователь {user_id} установил язык {lang}")
        return True
    
    def get_language_options(self) -> Dict[str, str]:
        """
        Получение всех поддерживаемых языков с их отображаемыми названиями.
        
        Returns:
            Dict с кодами языков и их названиями
        """
        return self.SUPPORTED_LANGUAGES.copy()
    
    def is_locale_loaded(self, lang: str) -> bool:
        """
        Проверка, загружена ли локаль.
        
        Args:
            lang: Код языка
        
        Returns:
            True если локаль загружена
        """
        return lang in self._locales
    
    def reload_locales(self):
        """Перезагрузка всех файлов локализации с диска"""
        logger.info("Перезагрузка всех локалей...")
        self._locales.clear()
        self._load_locales()
    
    def reload_user_preferences(self):
        """Перезагрузка пользовательских предпочтений с диска"""
        logger.info("Перезагрузка предпочтений пользователей...")
        self._load_user_preferences()


# Глобальный экземпляр locale manager (инициализируется в bot.py)
_locale_manager: Optional[LocaleManager] = None


def init_locale_manager(locales_dir: str = None, user_prefs_file: str = None) -> LocaleManager:
    """
    Инициализация глобального экземпляра locale manager.
    
    Args:
        locales_dir: Путь к директории локалей
        user_prefs_file: Путь к файлу предпочтений пользователей
    
    Returns:
        Экземпляр LocaleManager
    """
    global _locale_manager
    _locale_manager = LocaleManager(locales_dir, user_prefs_file)
    return _locale_manager


def get_locale_manager() -> Optional[LocaleManager]:
    """
    Получение глобального экземпляра locale manager.
    
    Returns:
        Экземпляр LocaleManager или None если не инициализирован
    """
    return _locale_manager


def get_text(key: str, lang: str = None, **kwargs) -> str:
    """
    Функция-обертка для получения текста из глобального locale manager.
    
    Args:
        key: Ключ текста
        lang: Код языка
        **kwargs: Аргументы форматирования
    
    Returns:
        Локализованный текст
    """
    if _locale_manager is None:
        logger.error("Locale manager не инициализирован")
        return f"[{key}]"
    
    return _locale_manager.get_text(key, lang, **kwargs)
