@echo off
chcp 65001 >nul
echo ====================================================
echo           CONSULTA DE CNPJ EM MASSA
echo ====================================================
echo.

echo Verificando Python...

set PYTHON_CMD=

python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
    goto :run_program
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=py
    goto :run_program
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python3
    goto :run_program
)

echo ❌ Python não encontrado!
echo Execute primeiro: instalar_simples.bat
pause
exit /b 1

:run_program
echo Iniciando programa...
echo.
%PYTHON_CMD% consulta_cnpj.py

echo.
echo Programa finalizado.
echo Pressione qualquer tecla para fechar...
pause >nul