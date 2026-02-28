$url = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
$out = "$env:TEMP\python-3.12.10-amd64.exe"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
Start-Process -FilePath $out -ArgumentList "/passive","PrependPath=1","InstallAllUsers=0" -Wait
