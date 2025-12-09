param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Update"
)

$ErrorActionPreference = "Stop"

Write-Host "Adding all changes..." -ForegroundColor Cyan
git add -A

Write-Host "Committing with message: auto: $Message" -ForegroundColor Cyan
git commit -m "auto: $Message"

Write-Host "Pushing to remote..." -ForegroundColor Cyan
git push

Write-Host "Done!" -ForegroundColor Green
