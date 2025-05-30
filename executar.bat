@echo off
chcp 65001 >nul
echo ====================================================
echo           CONSULTA DE CNPJ EM MASSA
echo ====================================================
echo.

echo Ativando ambiente virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✓ Ambiente virtual ativado!
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute primeiro: instalar_corrigido.bat
    echo.
    pause
    exit /b 1
)

echo.
echo Iniciando programa...
echo.

REM Tenta diferentes comandos Python
python consulta_cnpj.py
if %errorlevel% == 0 goto :success

py consulta_cnpj.py  
if %errorlevel% == 0 goto :success

python3 consulta_cnpj.py
if %errorlevel% == 0 goto :success

echo ❌ Erro ao executar programa!
echo Verifique se o arquivo consulta_cnpj.py existe nesta pasta.
echo.
pause
exit /b 1

:success
echo.
echo ✅ Programa finalizado com sucesso!
echo Pressione qualquer tecla para fechar...
pause >nul