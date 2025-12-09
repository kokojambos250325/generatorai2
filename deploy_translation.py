#!/usr/bin/env python3
"""Deploy translation service to server"""
import paramiko
import os

# Read the translation service file
with open('telegram_bot/services/translation_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Connect to server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('38.147.83.26', username='root', port=35108, key_filename=os.path.expanduser('~/.ssh/id_rsa'))

# Create directory
stdin, stdout, stderr = ssh.exec_command('mkdir -p /workspace/telegram_bot/services')
stdout.channel.recv_exit_status()

# Write file
sftp = ssh.open_sftp()
remote_file = sftp.open('/workspace/telegram_bot/services/translation_service.py', 'w')
remote_file.write(content)
remote_file.close()
sftp.close()

print("✅ translation_service.py uploaded successfully")

# Install dependencies
print("\n📦 Installing dependencies...")
stdin, stdout, stderr = ssh.exec_command('cd /workspace && /workspace/venv/bin/pip install -q transformers sentencepiece protobuf')
exit_code = stdout.channel.recv_exit_status()

if exit_code == 0:
    print("✅ Dependencies installed")
else:
    print(f"⚠️ Installation exit code: {exit_code}")
    print(stderr.read().decode())

# Download M2M100 model
print("\n📥 Downloading M2M100 model (~1.2GB)...")
test_script = """
cd /workspace
python3 << 'PYEOF'
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
print("Downloading model...")
tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
print("✅ Model downloaded")
# Test
tokenizer.src_lang = "ru"
text = "красивая девушка"
enc = tokenizer(text, return_tensors="pt")
gen = model.generate(**enc, forced_bos_token_id=tokenizer.get_lang_id("en"), max_length=50)
result = tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
print(f"Test: {text} → {result}")
PYEOF
"""

stdin, stdout, stderr = ssh.exec_command(test_script)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("Errors:", err)

ssh.close()
print("\n🎉 Translation service deployed!")
