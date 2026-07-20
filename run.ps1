$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Environnement absent. Exécutez .\build.ps1 pour préparer et valider le projet."
}
& $PythonExe -m app.main
