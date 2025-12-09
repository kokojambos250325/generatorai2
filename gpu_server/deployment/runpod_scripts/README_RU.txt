╔═══════════════════════════════════════════════════════════════╗
║   RunPod ComfyUI - Автоматический Запуск                     ║
╚═══════════════════════════════════════════════════════════════╝

✅ РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО!

Файлы успешно загружены на RunPod:
  📁 /workspace/.runpod/scripts/start.sh
  📁 /workspace/.runpod/runpod-entrypoint.sh
  📁 /workspace/.runpod/logs/ (для логов)

═══════════════════════════════════════════════════════════════

🔧 ЧТО ДАЛЬШЕ?

1️⃣ Откройте RunPod Web Terminal
   Перейдите в панель управления RunPod → ваш под → Connect → Web Terminal

2️⃣ Проверьте наличие ComfyUI:
   
   ls -la /workspace/ComfyUI

3️⃣ Проверьте наличие venv (виртуального окружения):
   
   ls -la /workspace/ComfyUI/venv

   Если venv НЕТ, создайте его:
   
   cd /workspace/ComfyUI
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

4️⃣ Протестируйте ручной запуск ComfyUI:
   
   bash /workspace/.runpod/scripts/start.sh

   Вы должны увидеть:
   ✓ ComfyUI is running successfully
   
5️⃣ Проверьте, что процесс запущен:
   
   ps aux | grep main.py

   Должна быть строка с "python main.py --listen 0.0.0.0 --port 8188"

6️⃣ Проверьте логи:
   
   cat /workspace/.runpod/logs/comfyui.log

   или в реальном времени:
   
   tail -f /workspace/.runpod/logs/comfyui.log

7️⃣ Проверьте доступ к веб-интерфейсу:
   
   Откройте в браузере:
   https://<POD_ID>-8188.proxy.runpod.net
   
   (адрес найдёте в RunPod панели в разделе Connect)

═══════════════════════════════════════════════════════════════

🔄 ТЕСТИРОВАНИЕ АВТОЗАПУСКА

1. Остановите под через RunPod панель
2. Запустите под снова
3. Подождите 30-60 секунд
4. Подключитесь через Web Terminal
5. Проверьте:

   # Процесс должен быть запущен
   ps aux | grep main.py
   
   # Логи должны быть свежие
   cat /workspace/.runpod/logs/entrypoint.log
   cat /workspace/.runpod/logs/comfyui.log
   
   # UI должен быть доступен
   curl http://localhost:8188

═══════════════════════════════════════════════════════════════

📝 ПОЛЕЗНЫЕ КОМАНДЫ

🟢 Запустить ComfyUI вручную:
   bash /workspace/.runpod/scripts/start.sh

🔴 Остановить ComfyUI:
   kill $(cat /workspace/.runpod/comfyui.pid)

🔄 Перезапустить ComfyUI:
   kill $(cat /workspace/.runpod/comfyui.pid)
   bash /workspace/.runpod/scripts/start.sh

📊 Посмотреть логи в реальном времени:
   tail -f /workspace/.runpod/logs/comfyui.log

📋 Проверить статус:
   ps aux | grep main.py

═══════════════════════════════════════════════════════════════

📂 СТРУКТУРА ФАЙЛОВ

/workspace/
├── .runpod/
│   ├── scripts/
│   │   └── start.sh              ← Скрипт запуска ComfyUI
│   ├── logs/
│   │   ├── entrypoint.log        ← Логи автозапуска
│   │   └── comfyui.log           ← Логи ComfyUI
│   ├── runpod-entrypoint.sh      ← Автозапуск при старте пода
│   └── comfyui.pid               ← ID процесса
└── ComfyUI/
    ├── venv/                     ← Python виртуальное окружение
    ├── main.py                   ← Основной файл ComfyUI
    └── ...

═══════════════════════════════════════════════════════════════

🎯 КРИТЕРИИ УСПЕХА

После настройки должно быть:

✅ ComfyUI автоматически запускается при старте пода
✅ Процесс виден в `ps aux | grep main.py`
✅ Логи записываются в /workspace/.runpod/logs/comfyui.log
✅ Веб-интерфейс доступен на порту 8188
✅ Нет блокирующих процессов (tail -f, sleep, etc.)
✅ Работает после рестарта пода

═══════════════════════════════════════════════════════════════

❓ РЕШЕНИЕ ПРОБЛЕМ

🔴 ComfyUI не запускается после рестарта:

   1. Проверьте логи:
      cat /workspace/.runpod/logs/entrypoint.log
      cat /workspace/.runpod/logs/comfyui.log
   
   2. Запустите вручную:
      bash /workspace/.runpod/scripts/start.sh

🔴 Ошибка "venv not found":

   cd /workspace/ComfyUI
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

🔴 Порт 8188 занят:

   # Найдите и убейте процесс
   lsof -ti:8188 | xargs kill -9
   
   # Перезапустите
   bash /workspace/.runpod/scripts/start.sh

🔴 Нет прав на выполнение:

   chmod +x /workspace/.runpod/scripts/start.sh
   chmod +x /workspace/.runpod/runpod-entrypoint.sh

═══════════════════════════════════════════════════════════════

📞 SSH ДОСТУП

Подключение:
  ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519

Повторное развёртывание (если нужно):
  powershell -ExecutionPolicy Bypass -File deploy.ps1

═══════════════════════════════════════════════════════════════

Создано: 2025-12-06
Версия: 1.0

═══════════════════════════════════════════════════════════════
