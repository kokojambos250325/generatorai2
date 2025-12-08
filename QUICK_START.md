# 🚀 БЫСТРАЯ ИНСТРУКЦИЯ ПО РАЗВЕРТЫВАНИЮ MVP НА RUNPOD

## ✅ ЧТО УЖЕ СДЕЛАНО

- Код запушен в GitHub: https://github.com/kokojambos250325/generatorai2
- Все файлы готовы к развертыванию
- Создан единый скрипт установки

## 📋 ЧТО НУЖНО СДЕЛАТЬ (3 шага)

### Шаг 1: Подключитесь к POD

Откройте терминал и выполните:

```bash
ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519
```

### Шаг 2: Скопируйте и вставьте скрипт

Откройте файл `DEPLOY_TO_POD.sh` в текстовом редакторе, скопируйте **ВСЁ** содержимое и вставьте в терминал POD.

Или выполните команды по частям:

```bash
# На POD выполните:
cd /workspace
git clone https://github.com/kokojambos250325/generatorai2.git temp_repo
cp -r temp_repo/backend temp_repo/gpu_server temp_repo/startup.sh temp_repo/infra ./
rm -rf temp_repo
mkdir -p logs models workflows

# Создание venv и установка зависимостей
python3 -m venv venv
source venv/bin/activate

cd backend && pip install -r requirements.txt
cd ../gpu_server && pip install -r requirements.txt
cd /workspace

# Настройка окружения
cp backend/.env.template backend/.env
cp gpu_server/.env.template gpu_server/.env
chmod +x startup.sh

# Запуск сервисов
./startup.sh
```

### Шаг 3: Проверьте работу

Подождите 15 секунд, затем проверьте:

```bash
# Проверка здоровья backend
curl http://localhost:8000/health

# Проверка здоровья GPU сервера
curl http://localhost:8001/health
```

**Ожидаемый результат:**
```json
// Backend
{"status":"healthy","gpu_available":true,"version":"1.0.0"}

// GPU Server  
{"status":"healthy","comfyui_available":false,"service":"gpu_server","version":"1.0.0"}
```

## 📊 Проверка логов

```bash
# Просмотр логов backend
tail -f /workspace/logs/backend.log

# Просмотр логов GPU server
tail -f /workspace/logs/gpu_server.log

# Проверка процессов
ps aux | grep -E "(uvicorn|python.*server.py)"
```

## 🔄 Перезапуск сервисов

```bash
cd /workspace
source venv/bin/activate
./startup.sh
```

## ✅ Что должно быть на POD после развертывания:

```
/workspace/
├── backend/          ✓ FastAPI backend
├── gpu_server/       ✓ GPU service  
├── infra/            ✓ SSH manager
├── logs/             ✓ Логи сервисов
├── models/           ✓ Для моделей (пусто пока)
├── workflows/        ✓ Для workflow (пусто пока)
├── venv/             ✓ Python окружение
└── startup.sh        ✓ Стартовый скрипт
```

## 🎯 Success Criteria

- ✅ `curl localhost:8000/health` возвращает 200 OK
- ✅ `curl localhost:8001/health` возвращает 200 OK
- ✅ Логи показывают запущенные сервисы
- ✅ Процессы uvicorn и python server.py работают

---

## 💡 Полезные команды

```bash
# Просмотр структуры
ls -R /workspace/backend
ls -R /workspace/gpu_server

# Просмотр конфигурации
cat /workspace/backend/.env
cat /workspace/gpu_server/.env

# Остановка сервисов
kill $(cat /workspace/backend.pid)
kill $(cat /workspace/gpu_server.pid)

# Проверка портов
netstat -tlnp | grep -E "8000|8001"
```

---

**Время установки:** ~5-10 минут (зависит от скорости загрузки зависимостей)

**После успешной установки можно сразу тестировать API!**
