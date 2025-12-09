"""
Direct file sync to server using paramiko
"""
import paramiko
import os

# Files to sync
FILES_TO_SYNC = [
    ("backend/schemas/response_generate.py", "/workspace/backend/schemas/response_generate.py"),
    ("backend/clients/gpu_client.py", "/workspace/backend/clients/gpu_client.py"),
    ("backend/services/generation_router.py", "/workspace/backend/services/generation_router.py"),
]

def sync_files():
    """Sync files to RunPod server"""
    # Load SSH config
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect using ~/.ssh/config alias 'runpod'
        ssh.connect('runpod')
        print("✅ Connected to RunPod server")
        
        sftp = ssh.open_sftp()
        
        for local_path, remote_path in FILES_TO_SYNC:
            if os.path.exists(local_path):
                print(f"\n📤 Uploading: {local_path} → {remote_path}")
                sftp.put(local_path, remote_path)
                print(f"✅ Uploaded successfully")
            else:
                print(f"❌ Local file not found: {local_path}")
        
        sftp.close()
        
        # Restart backend
        print("\n🔄 Restarting backend...")
        stdin, stdout, stderr = ssh.exec_command(
            "pkill -f 'uvicorn main:app' && sleep 2 && "
            "cd /workspace/backend && "
            "nohup /workspace/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 "
            "> /workspace/logs/backend.log 2>&1 &"
        )
        
        # Wait a bit and check logs
        print("⏳ Waiting 5 seconds...")
        import time
        time.sleep(5)
        
        stdin, stdout, stderr = ssh.exec_command("tail -15 /workspace/logs/backend.log")
        log_output = stdout.read().decode()
        print("\n📋 Backend logs:")
        print(log_output)
        
        if "Application startup complete" in log_output:
            print("\n✅ Backend started successfully!")
        else:
            print("\n⚠️  Backend may have issues, check logs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    sync_files()
