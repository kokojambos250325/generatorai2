@echo off
echo ========================================
echo Installing Translation Service on Server
echo ========================================

echo.
echo Step 1: Installing Python dependencies...
ssh runpod "/workspace/venv/bin/pip install -q transformers sentencepiece protobuf && echo Dependencies installed"

echo.
echo Step 2: Testing transformers installation...
ssh runpod "/workspace/venv/bin/python3 -c \"from transformers import M2M100Tokenizer; print('Transformers OK')\""

echo.
echo Step 3: Downloading M2M100 model (this may take 5-10 minutes)...
ssh runpod "/workspace/venv/bin/python3 -c \"from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer; print('Downloading...'); t=M2M100Tokenizer.from_pretrained('facebook/m2m100_418M'); m=M2M100ForConditionalGeneration.from_pretrained('facebook/m2m100_418M'); print('Model downloaded!')\""

echo.
echo Step 4: Testing translation...
ssh runpod "/workspace/venv/bin/python3 -c \"from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer; t=M2M100Tokenizer.from_pretrained('facebook/m2m100_418M'); m=M2M100ForConditionalGeneration.from_pretrained('facebook/m2m100_418M'); t.src_lang='ru'; text='красивая девушка'; enc=t(text, return_tensors='pt'); gen=m.generate(**enc, forced_bos_token_id=t.get_lang_id('en'), max_length=30); result=t.batch_decode(gen, skip_special_tokens=True)[0]; print(f'Test: {text} -> {result}')\""

echo.
echo Step 5: Restarting Telegram bot...
ssh runpod "pkill -f 'python bot.py' ; sleep 2 ; cd /workspace/telegram_bot && nohup python bot.py > /workspace/logs/bot.log 2>&1 & sleep 2 && echo 'Bot restarted'"

echo.
echo Step 6: Checking bot status...
ssh runpod "ps aux | grep 'python bot.py' | grep -v grep"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
pause
