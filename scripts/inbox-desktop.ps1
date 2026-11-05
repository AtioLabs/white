# Put a "White Inbox" folder on the founder's Desktop and make White watch it.
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Inbox = Join-Path $Desktop "White Inbox"
New-Item -ItemType Directory -Force $Inbox | Out-Null
$cfg = Join-Path $ProfileHome "founder\inbox.yaml"
$lines = @()
if (Test-Path $cfg) { $lines = Get-Content $cfg }
if (-not ($lines -match [regex]::Escape($Inbox))) {
  if (-not ($lines -match "^folders:")) { $lines += "folders:" }
  $lines += "  - $Inbox"
  Set-Content -Path $cfg -Value $lines -Encoding utf8
}
# Move anything already dropped in the hidden profile inbox to the Desktop one.
$old = Join-Path $ProfileHome "founder\inbox"
Get-ChildItem $old -File -ErrorAction SilentlyContinue | Move-Item -Destination $Inbox -Force
Write-Host "White Inbox: $Inbox"
