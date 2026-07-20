$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $Uv = Get-Command uv -ErrorAction SilentlyContinue
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($Uv) { & uv venv --python 3.12 .venv }
    elseif ($PyLauncher) { & py -3.12 -m venv .venv }
    else { throw "Python 3.12 ou uv est requis pour créer l’environnement." }
}

$RequiredBinaries = @("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe")
$MissingBinaries = $RequiredBinaries | Where-Object { -not (Test-Path (Join-Path $ProjectRoot "bin\$_")) }
if ($MissingBinaries) { throw "Binaires manquants dans bin: $($MissingBinaries -join ', ')" }

& $PythonExe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "L’installation des dépendances a échoué." }
& $PythonExe -m ruff check app tests
if ($LASTEXITCODE -ne 0) { throw "Ruff a détecté des erreurs; build arrêté." }
& $PythonExe -m pytest
if ($LASTEXITCODE -ne 0) { throw "Les tests ont échoué; build arrêté." }
$BuildPath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot "build"))
$DistPath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
if (-not $BuildPath.StartsWith([IO.Path]::GetFullPath($ProjectRoot)) -or -not $DistPath.StartsWith([IO.Path]::GetFullPath($ProjectRoot))) { throw "Chemins de build non sûrs." }
if (Test-Path $BuildPath) { Remove-Item -LiteralPath $BuildPath -Recurse -Force }
if (Test-Path $DistPath) { Remove-Item -LiteralPath $DistPath -Recurse -Force }
& $PythonExe -m PyInstaller --noconfirm mediagrab.spec
$Result = Join-Path $ProjectRoot "dist\MediaGrab\MediaGrab.exe"
if (-not (Test-Path $Result)) { throw "L’exécutable final est introuvable." }
Write-Host "Build terminé: $Result"
