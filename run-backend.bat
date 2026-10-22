@echo off
REM Start the local Django API with CORS enabled for the deployed Firebase site
REM and for any localtunnel host (the tunnel URL changes on every restart).
set DJANGO_CORS_ALLOWED_ORIGINS=https://new-school-management-system.web.app
set DJANGO_CORS_ALLOWED_ORIGIN_REGEXES=https://.*\.loca\.lt,https://.*\.trycloudflare\.com
cd /d "C:\Users\user\Downloads\New School Management System\backend"
"C:\Users\user\Downloads\New School Management System\.venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000 --noreload
