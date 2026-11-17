@echo off
cd /d "%~dp0"
if not exist main.py (
echo Put this BAT file in the constructor folder, next to main.py.
pause
exit /b 1
)
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $out=Join-Path $root 'sources_090.txt'; $utf8=New-Object System.Text.UTF8Encoding($false); $writer=New-Object System.IO.StreamWriter($out,$false,$utf8); try { $folders=@('editor','engine','project','support','tests'); $files=@(); foreach($folder in $folders) { $p=Join-Path $root $folder; if(Test-Path -LiteralPath $p) { $files+=Get-ChildItem -LiteralPath $p -Recurse -File | Where-Object { $_.Extension -eq '.py' -and $_.FullName -notmatch '[\/]__pycache__[\/]' } } }; $names=@('main.py','requirements.txt','AI_HANDOFF_RU.md','PROJECT_MAP.md','KNOWN_ISSUES.md','TEST_STATUS_RU.md','README_RU.md','assets\profiles.json','assets\demo_project.json'); foreach($name in $names) { $p=Join-Path $root $name; if(Test-Path -LiteralPath $p) { $files+=Get-Item -LiteralPath $p } }; foreach($file in ($files | Sort-Object FullName -Unique)) { $relative=$file.FullName.Substring($root.Length).TrimStart([char]92); $writer.WriteLine('===== FILE: '+$relative+' ====='); $writer.WriteLine([System.IO.File]::ReadAllText($file.FullName)); $writer.WriteLine() } } finally { $writer.Dispose() }; Write-Host 'Created sources_090.txt. Attach that text file to the chat.'"
if errorlevel 1 echo Collection failed. Copy the error text.
pause
