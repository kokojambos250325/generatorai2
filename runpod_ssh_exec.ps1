# RunPod SSH Remote Command Execution
param(
    [Parameter(Mandatory=$true)]
    [string]$Command
)

$SSH_USER = "p8q2agahufxw4a-64410d8e"
$SSH_HOST = "ssh.runpod.io"
$SSH_KEY = "$env:USERPROFILE\.ssh\id_ed25519"

Write-Host "Executing on RunPod: $Command" -ForegroundColor Cyan

ssh -T $SSH_USER@$SSH_HOST -i $SSH_KEY $Command
