docker ps
New-Item -ItemType Directory -Force "C:\Users\Giorgio\Desktop\my-projects\backup" | Out-Null
docker cp my-postgres:/app/data/app.db "C:\Users\Giorgio\Desktop\my-projects\backup\app_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"