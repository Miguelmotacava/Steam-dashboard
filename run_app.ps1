# Script para ejecutar el Steam Dashboard
# Ejecutar desde la raíz del proyecto: .\run_app.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $scriptDir "App_streamlit"

# Activar entorno virtual si existe
$venvPath = Join-Path $scriptDir "steam-dashboard-env\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

Set-Location $appDir
streamlit run app_steam.py
