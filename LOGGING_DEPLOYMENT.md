# Инструкция по развертыванию логирования

## Обзор

Все необходимые файлы с логированием готовы к загрузке и тестированию.

## Файлы для загрузки на сервер

### 1. Уже загруженные файлы ✓

- `backend/services/free_generation.py` - загружен 2025-12-09 01:31:28 (160 строк)
- `gpu_server/comfy_client.py` - загружен 2025-12-09 01:42:00 (17KB)

### 2. Файлы, ожидающие загрузки

Загрузите следующие файлы на сервер:

```bash
# 1. Обновленный startup.sh с запуском ComfyUI
scp -P 35108 "c:\projekt\generator -ai\startup.sh" root@38.147.83.26:/workspace/startup.sh

# 2. Скрипт перезапуска сервисов
scp -P 35108 "c:\projekt\generator -ai\restart_services.sh" root@38.147.83.26:/workspace/restart_services.sh

# 3. Скрипт тестирования логирования
scp -P 35108 "c:\projekt\generator -ai\test_logging.sh" root@38.147.83.26:/workspace/test_logging.sh
```

## Шаги развертывания

### Шаг 1: Загрузите файлы (см. выше)

### Шаг 2: Сделайте скрипты исполняемыми

```bash
ssh -p 35108 root@38.147.83.26
cd /workspace
chmod +x startup.sh restart_services.sh test_logging.sh
```

### Шаг 3: Перезапустите сервисы

```bash
# Вариант А: Полный перезапуск с ComfyUI
cd /workspace
./startup.sh

# Вариант Б: Только backend и GPU server (если ComfyUI уже запущен)
cd /workspace
./restart_services.sh
```

### Шаг 4: Проверьте статус сервисов

```bash
# Проверка здоровья
curl http://localhost:8000/health  # Backend
curl http://localhost:8002/health  # GPU Server
curl http://localhost:8188/system_stats  # ComfyUI

# Проверка процессов
ps aux | grep python
cat /workspace/*.pid
```

### Шаг 5: Запустите тест логирования

```bash
cd /workspace
./test_logging.sh
```

## Что было реализовано

### Backend (free_generation.py)

✅ **6 типов событий логирования:**
- `generate_request` - входящий запрос
- `validation_error` - ошибка валидации
- `gpu_request` - запрос к GPU серверу
- `gpu_response` - ответ от GPU сервера
- `timeout_error` - таймаут
- `response_sent` - ответ отправлен клиенту

✅ **UUID v4 request_id** для трассировки

✅ **JSON Lines формат** в `/workspace/logs/backend.log`

### GPU Server (comfy_client.py)

✅ **8 типов событий логирования:**
- `workflow_loaded` - workflow загружен (с подсчетом узлов)
- `comfyui_prompt_sent` - промпт отправлен в ComfyUI
- `comfyui_polling` - прогресс опроса (каждые 10 попыток)
- `comfyui_complete` - завершение генерации (с duration_ms)
- `image_retrieved` - изображение получено (с размером файла)
- `error_workflow` - ошибка загрузки workflow
- `error_comfyui` - ошибка ComfyUI API

✅ **UUID v4 generation_id** для трассировки

✅ **Передача request_id и generation_id** через всю цепочку

✅ **JSON Lines формат** в `/workspace/logs/gpu_server.log`

### ComfyUI Logging (startup.sh)

✅ **Запуск ComfyUI** перед GPU Server

✅ **Перенаправление логов** в `/workspace/logs/comfyui.log`

✅ **Проверка здоровья** после запуска

✅ **Мониторинг статуса** в выводе скрипта

## Структура логов

```
/workspace/logs/
├── backend.log        # Backend события (JSON Lines)
├── gpu_server.log     # GPU Server события (JSON Lines)
├── comfyui.log        # ComfyUI stdout/stderr (plain text)
├── telegram_bot.log   # Telegram bot события (будет в Phase 2)
└── startup.log        # Лог запуска сервисов
```

## Примеры использования

### Проверка последних событий

```bash
# Последние 10 backend событий
tail -10 /workspace/logs/backend.log | jq '.'

# Последние 10 GPU server событий
tail -10 /workspace/logs/gpu_server.log | jq '.'

# Поиск ошибок
grep '"level": "ERROR"' /workspace/logs/backend.log | tail -10
grep '"level": "ERROR"' /workspace/logs/gpu_server.log | tail -10
```

### Трассировка запроса

```bash
# По request_id
REQUEST_ID="ваш-request-id"
grep "$REQUEST_ID" /workspace/logs/backend.log
grep "$REQUEST_ID" /workspace/logs/gpu_server.log

# По generation_id
GENERATION_ID="ваш-generation-id"
grep "$GENERATION_ID" /workspace/logs/gpu_server.log
```

### Анализ производительности

```bash
# Среднее время генерации
grep '"event": "comfyui_complete"' /workspace/logs/gpu_server.log | \
  grep -o '"duration_ms": [0-9]*' | \
  awk '{sum+=$2; count++} END {print "Average:", sum/count, "ms"}'

# Медленные генерации (> 60 секунд)
grep '"event": "comfyui_complete"' /workspace/logs/gpu_server.log | \
  grep -E '"duration_ms": [6-9][0-9]{4}'
```

## Устранение неполадок

### Проблема: Логи не создаются

**Решение:**
```bash
# Проверьте директорию логов
ls -la /workspace/logs/

# Создайте директорию, если её нет
mkdir -p /workspace/logs

# Проверьте права доступа
chmod 755 /workspace/logs
```

### Проблема: События не логируются

**Решение:**
```bash
# Проверьте, что новый код загружен
stat /workspace/backend/services/free_generation.py
stat /workspace/gpu_server/comfy_client.py

# Перезапустите сервисы
cd /workspace
./restart_services.sh

# Проверьте логи на ошибки
tail -50 /workspace/logs/backend.log
tail -50 /workspace/logs/gpu_server.log
```

### Проблема: ComfyUI не стартует

**Решение:**
```bash
# Проверьте, запущен ли ComfyUI
curl http://localhost:8188/system_stats

# Запустите вручную
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 >> /workspace/logs/comfyui.log 2>&1 &

# Сохраните PID
echo $! > /workspace/comfyui.pid

# Проверьте логи
tail -f /workspace/logs/comfyui.log
```

## Следующие шаги

После успешного тестирования логирования:

1. **Phase 2:** Реализовать logging для Telegram Bot (9 типов событий)
2. **Phase 3:** Реализовать режимы Remove Clothes и NSFW Face
3. **Phase 4:** Интеграция и E2E тестирование

## Соответствие спецификации

Все реализованное соответствует:
- **Раздел 11.3** дизайн-документа: Backend Logging
- **Раздел 11.4** дизайн-документа: GPU Server Logging
- **Раздел 11.5** дизайн-документа: ComfyUI Logging
- **Раздел 11.9** дизайн-документа: Integration with Existing Workflow (Phase 1)

## Контакты при проблемах

При возникновении проблем проверьте:
1. Логи сервисов: `/workspace/logs/*.log`
2. Статус процессов: `ps aux | grep python`
3. Сетевые порты: `netstat -tlnp | grep -E '8000|8002|8188'`
