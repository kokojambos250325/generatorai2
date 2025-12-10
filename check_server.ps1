# Quick server check script
$sshKey = "$env:USERPROFILE\.ssh\id_ed25519"
$server = "root@38.147.83.26"
$port = "35108"

Write-Host "Checking SSH key..."
if (Test-Path $sshKey) {
    Write-Host "SSH key found: $sshKey"
} else {
    Write-Host "SSH key NOT found: $sshKey"
    exit 1
}

Write-Host "`nConnecting to server..."
ssh -i $sshKey -p $port $server "cd /workspace && pwd && echo '---' && ls -la | head -20"

