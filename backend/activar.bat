@echo off
REM Activa el venv AISLADO del proyecto (no instala nada global)
call "%~dp0venv\Scripts\activate.bat"
echo Venv activado: %VIRTUAL_ENV%
echo Comandos: python manage.py migrate / python manage.py runserver
cmd /k
