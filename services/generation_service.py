from typing import Any, Dict
from client_gpu import GPUClient
from config import Settings, get_settings
from models.generation_request import GenerationRequest
from logger.generation_logger import GenerationLogger
from pipelines.registry import get_pipeline_by_mode
from gpu_server.schema import GPUGenerationRequest
from storage.temp_storage import TempStorage
from models.model_manager import ModelManager


class GenerationService:
    """Сервис для управления процессом генерации"""

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        self.gpu_client = GPUClient(
            base_url=self.settings.GPU_SERVER_URL,
            api_key=self.settings.GPU_SERVER_API_KEY,
            timeout=self.settings.TIMEOUT_GENERATION
        )
        self.logger = GenerationLogger(output_format="console")
        self.temp_storage = TempStorage()
        # Создание единого экземпляра ModelManager для всех пайплайнов
        self.model_manager = ModelManager(device="cuda")

    async def start_generation(self, task_type: str, params: Dict[str, Any]) -> str:
        """Запуск процесса генерации"""
        pass

    async def poll_generation(self, task_id: str) -> Dict[str, Any]:
        """Опрос статуса генерации"""
        pass

    async def fetch_result(self, task_id: str) -> Any:
        """Получение результата генерации"""
        pass

    async def process_task(self, task_id: str, request: GenerationRequest) -> Any:
        """
        Обработка задачи генерации
        
        Выполняет полный цикл генерации:
        1. Выбор нужного пайплайна на основе request.mode
        2. Загрузка моделей пайплайна
        3. Подготовка входных данных
        4. Выполнение генерации
        
        Args:
            task_id: Уникальный ID задачи
            request: Параметры генерации
            
        Returns:
            Результат генерации (изображение в base64 или другие данные)
        """
        # Логирование начала обработки
        self.logger.log_start(
            task_id=task_id,
            task_type=request.mode,
            params=request.model_dump()
        )
        
        try:
            # Создание пайплайна с передачей ModelManager
            pipeline = get_pipeline_by_mode(
                mode=request.mode,
                device="cuda",
                model_manager=self.model_manager
            )
            
            if pipeline is None:
                error_msg = f"Unknown generation mode: {request.mode}"
                self.logger.log_error(
                    task_id=task_id,
                    error=error_msg
                )
                raise ValueError(error_msg)
            
            # Сохранение входных изображений во временное хранилище
            self.logger.log_update(
                task_id=task_id,
                status="saving_inputs",
                message="Saving input images to temp storage"
            )
            
            temp_paths = {}
            
            # Сохранение базового изображения
            if request.image:
                temp_paths['image_path'] = self.temp_storage.save_temp_image(
                    request.image,
                    f"{task_id}_input.png"
                )
            
            # Сохранение изображения лица
            if request.face_image:
                temp_paths['face_image_path'] = self.temp_storage.save_temp_image(
                    request.face_image,
                    f"{task_id}_face.png"
                )
            
            # Сохранение изображения одежды
            if request.clothes_image:
                temp_paths['clothes_image_path'] = self.temp_storage.save_temp_image(
                    request.clothes_image,
                    f"{task_id}_clothes.png"
                )
            
            # Логирование начала загрузки моделей
            self.logger.log_update(
                task_id=task_id,
                status="loading_models",
                message="Loading pipeline models"
            )
            
            # Загрузка моделей пайплайна
            await pipeline.load_models()
            
            # Логирование завершения загрузки моделей
            self.logger.log_update(
                task_id=task_id,
                status="models_loaded",
                message="Pipeline models loaded successfully"
            )
            
            # Логирование подготовки входных данных
            self.logger.log_update(
                task_id=task_id,
                status="preparing_inputs",
                message="Preparing input data"
            )
            
            # Подготовка входных данных с путями вместо base64
            prepared_request = GenerationRequest(
                mode=request.mode,
                prompt=request.prompt,
                style=request.style,
                seed=request.seed,
                # Пути к временным файлам вместо base64
                image=temp_paths.get('image_path'),
                face_image=temp_paths.get('face_image_path'),
                clothes_image=temp_paths.get('clothes_image_path'),
                # Post-processing parameters
                quality_mode=request.quality_mode if hasattr(request, 'quality_mode') else "balanced",
                upscale=request.upscale if hasattr(request, 'upscale') else False,
                enhance_face=request.enhance_face if hasattr(request, 'enhance_face') else True
            )
            
            inputs = await pipeline.prepare_inputs(prepared_request)
            
            # Логирование завершения подготовки входных данных
            self.logger.log_update(
                task_id=task_id,
                status="inputs_prepared",
                message="Input data prepared successfully"
            )
            
            # Логирование начала генерации
            quality_mode = getattr(request, 'quality_mode', 'balanced')
            self.logger.log_update(
                task_id=task_id,
                status="generating",
                message=f"Running generation pipeline (quality: {quality_mode})"
            )
            
            # Выполнение генерации
            result = await pipeline.run(inputs)
            
            # Логирование завершения генерации
            self.logger.log_update(
                task_id=task_id,
                status="generation_complete",
                message="Generation completed successfully"
            )
            
            # Очистка временных файлов
            for temp_path in temp_paths.values():
                self.temp_storage.delete_temp(temp_path)
            
            # Логирование успешного завершения
            self.logger.log_finish(
                task_id=task_id,
                success=True,
                result=result
            )
            
            # Возвращаем результат генерации
            return result
            
        except Exception as e:
            # Логирование ошибки
            self.logger.log_error(
                task_id=task_id,
                error=str(e),
                exception=e
            )
            raise


