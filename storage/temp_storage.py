import os
import base64
from typing import Optional
from pathlib import Path


class TempStorage:
    """
    Хранилище для временных файлов изображений
    
    Управляет сохранением, загрузкой и удалением временных файлов.
    Использует локальное файловое хранилище в папке /tmp проекта.
    """
    
    def __init__(self, temp_dir: str = "tmp"):
        """
        Инициализация временного хранилища
        
        Args:
            temp_dir: Директория для временных файлов (относительно корня проекта)
        """
        self.temp_dir = Path(temp_dir)
        # Создание директории если не существует
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def save_temp_image(self, image_base64: str, filename: Optional[str] = None) -> str:
        """
        Сохранение изображения из base64 во временное хранилище
        
        Декодирует base64 строку и сохраняет как файл изображения.
        
        Args:
            image_base64: Изображение в формате base64
            filename: Имя файла (опционально, будет сгенерировано если не указано)
            
        Returns:
            Путь к сохранённому файлу
            
        Example:
            >>> storage = TempStorage()
            >>> path = storage.save_temp_image(base64_data, "temp_image.png")
        """
        # Генерация имени файла если не указано
        if filename is None:
            import uuid
            filename = f"{uuid.uuid4().hex}.png"
        
        file_path = self.temp_dir / filename
        
        # Декодирование base64 и сохранение
        image_data = base64.b64decode(image_base64)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return str(file_path)
    
    def load_temp_image(self, path: str) -> str:
        """
        Загрузка изображения из временного хранилища в base64
        
        Читает файл и кодирует его содержимое в base64.
        
        Args:
            path: Путь к файлу изображения
            
        Returns:
            Изображение в формате base64
            
        Raises:
            FileNotFoundError: Если файл не найден
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        
        # Чтение и кодирование в base64
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        return base64.b64encode(image_data).decode('utf-8')
    
    def delete_temp(self, path: str) -> bool:
        """
        Удаление временного файла
        
        Args:
            path: Путь к файлу для удаления
            
        Returns:
            True если файл успешно удалён, False в противном случае
        """
        try:
            file_path = Path(path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            # Логирование ошибки удаления (пока просто возврат False)
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Очистка старых временных файлов
        
        Удаляет файлы старше указанного времени.
        
        Args:
            max_age_hours: Максимальный возраст файлов в часах
            
        Returns:
            Количество удалённых файлов
        """
        import time
        
        deleted_count = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        pass
        
        return deleted_count
