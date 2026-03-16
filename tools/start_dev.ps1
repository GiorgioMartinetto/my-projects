# Vai alla directory root del progetto (parent della cartella tools)
Set-Location -Path $PSScriptRoot\..

# Entra nella cartella app
Set-Location -Path app

# Avvia uvicorn con reload
uvicorn src.main:app --reload

