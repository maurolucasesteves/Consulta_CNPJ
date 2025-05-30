@echo off
chcp 65001 >nul
echo ====================================================
echo        CONSULTA DE CNPJ - SISTEMA COMPLETO
echo ====================================================
echo         INSTALA E EXECUTA AUTOMATICAMENTE
echo                  VERSAO UNICA
echo ====================================================
echo.

REM ==================================================
REM CONFIGURAÇÕES
REM ==================================================
set USAR_AMBIENTE_VIRTUAL=1
set PYTHON_CMD=
set MODO_EXECUCAO=

echo [ETAPA 1/8] Verificando Python...

REM Detecta Python (prioriza py -3)
py -3 --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=py -3
    echo ✓ Python encontrado: py -3
    goto :check_version
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=py
    echo ✓ Python encontrado: py
    goto :check_version
)

python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
    echo ⚠️  Python encontrado: python
    
    REM Verifica Microsoft Store
    python -c "import sys; print(sys.executable)" 2>nul | findstr /i "WindowsApps" >nul
    if %errorlevel% == 0 (
        echo ❌ ERRO: Python do Microsoft Store!
        echo.
        echo 💡 SOLUÇÕES:
        echo 1. Desabilite em: Configurações > Apps > Aliases de execução
        echo 2. Instale Python de: https://python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    goto :check_version
)

echo ❌ ERRO: Python não encontrado!
echo.
echo 📥 INSTALE PYTHON:
echo 1. https://python.org/downloads/
echo 2. MARQUE "Add Python to PATH" na instalação
echo 3. Execute este script novamente
echo.
pause
exit /b 1

:check_version
REM Verifica versão do Python
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Versão do Python: %PYTHON_VERSION%

REM Verifica se é Python 3.13+ (precisa de bibliotecas mais novas)
echo %PYTHON_VERSION% | findstr /r "3\.1[3-9]" >nul
if %errorlevel% == 0 (
    echo ⚠️  Python 3.13+ detectado - usando bibliotecas compatíveis
    set PANDAS_VERSION=pandas
    set REQUESTS_VERSION=requests
    set OPENPYXL_VERSION=openpyxl
) else (
    echo ✓ Python compatível - usando versões específicas
    set PANDAS_VERSION=pandas==2.1.4
    set REQUESTS_VERSION=requests==2.31.0
    set OPENPYXL_VERSION=openpyxl==3.1.2
)

echo.
echo [ETAPA 2/8] Verificando arquivos necessários...

REM Verifica se consulta_cnpj.py existe
if not exist "consulta_cnpj.py" (
    echo ❌ ERRO: Arquivo consulta_cnpj.py não encontrado!
    echo Certifique-se que está na pasta correta.
    pause
    exit /b 1
)
echo ✓ consulta_cnpj.py encontrado

REM Verifica se CNPJ.xlsx existe
if not exist "CNPJ.xlsx" (
    echo ⚠️  AVISO: Arquivo CNPJ.xlsx não encontrado
    echo Coloque seu arquivo Excel com os CNPJs nesta pasta
    echo Nome deve ser exatamente: CNPJ.xlsx
    echo.
    choice /c SN /m "Continuar mesmo assim (S/N)?"
    if errorlevel 2 exit /b 1
) else (
    echo ✓ CNPJ.xlsx encontrado
)

echo.
echo [ETAPA 3/8] Escolhendo modo de instalação...

REM Verifica se já existe ambiente virtual
if exist "venv\Scripts\activate.bat" (
    echo ✓ Ambiente virtual existe - tentando usar
    set MODO_EXECUCAO=venv
    goto :activate_venv
)

REM Verifica se bibliotecas já estão instaladas globalmente
%PYTHON_CMD% -c "import pandas; import requests; import openpyxl; print('OK')" >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Bibliotecas já instaladas globalmente
    set MODO_EXECUCAO=global
    goto :run_program
)

REM Pergunta qual modo usar
echo.
echo Escolha o modo de instalação:
echo 1. Ambiente Virtual (Recomendado - mais seguro)
echo 2. Global (Mais simples - instala no sistema)
echo.
choice /c 12 /m "Escolha (1 ou 2):"
if errorlevel 2 (
    set MODO_EXECUCAO=global
    goto :install_global
) else (
    set MODO_EXECUCAO=venv
    goto :create_venv
)

REM ==================================================
REM INSTALAÇÃO COM AMBIENTE VIRTUAL
REM ==================================================
:create_venv
echo.
echo [ETAPA 4/8] Criando ambiente virtual...

REM Remove ambiente virtual anterior se existir
if exist "venv" (
    echo Removendo ambiente virtual anterior...
    rmdir /s /q venv >nul 2>&1
)

%PYTHON_CMD% -m venv venv
if errorlevel 1 (
    echo ❌ ERRO: Falha ao criar ambiente virtual!
    echo Tentando instalação global...
    set MODO_EXECUCAO=global
    goto :install_global
)
echo ✓ Ambiente virtual criado

:activate_venv
echo.
echo [ETAPA 5/8] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERRO: Falha ao ativar ambiente virtual!
    echo Tentando instalação global...
    set MODO_EXECUCAO=global
    goto :install_global
)
echo ✓ Ambiente virtual ativado

echo.
echo [ETAPA 6/8] Instalando bibliotecas no ambiente virtual...
goto :install_libraries

REM ==================================================
REM INSTALAÇÃO GLOBAL
REM ==================================================
:install_global
echo.
echo [ETAPA 4/8] Instalação global selecionada...
echo [ETAPA 5/8] Pulando criação de ambiente virtual...
echo.
echo [ETAPA 6/8] Instalando bibliotecas globalmente...

:install_libraries
echo Atualizando pip...
python -m pip install --upgrade pip >nul 2>&1

echo Instalando pandas...
pip install %PANDAS_VERSION%
if errorlevel 1 (
    echo ❌ ERRO ao instalar pandas!
    echo Tentando versão alternativa...
    pip install pandas --no-build-isolation
    if errorlevel 1 (
        echo ❌ Falha definitiva ao instalar pandas!
        goto :install_error
    )
)
echo ✓ pandas instalado

echo Instalando requests...
pip install %REQUESTS_VERSION%
if errorlevel 1 (
    echo ❌ ERRO ao instalar requests!
    goto :install_error
)
echo ✓ requests instalado

echo Instalando openpyxl...
pip install %OPENPYXL_VERSION%
if errorlevel 1 (
    echo ❌ ERRO ao instalar openpyxl!
    goto :install_error
)
echo ✓ openpyxl instalado

echo.
echo [ETAPA 7/8] Testando bibliotecas...
python -c "import pandas; import requests; import openpyxl; print('✓ Todas as bibliotecas funcionando!')"
if errorlevel 1 (
    echo ❌ ERRO: Bibliotecas não funcionam!
    goto :install_error
)

echo.
echo [ETAPA 8/8] Iniciando programa...
echo ====================================================
echo           BIBLIOTECAS INSTALADAS COM SUCESSO!
echo ====================================================
echo.
echo ✅ Modo de instalação: %MODO_EXECUCAO%
echo ✅ Todas as bibliotecas funcionando
echo ✅ Iniciando programa de consulta CNPJ...
echo.
timeout /t 2 >nul

:run_program
python consulta_cnpj.py

if %errorlevel% == 0 (
    echo.
    echo ====================================================
    echo            PROGRAMA FINALIZADO COM SUCESSO!
    echo ====================================================
    echo.
    echo ✅ Consulta de CNPJs concluída
    echo 📄 Resultado salvo em: resultado_cnpj.xlsx
    echo.
) else (
    echo.
    echo ====================================================
    echo              ERRO AO EXECUTAR PROGRAMA
    echo ====================================================
    echo.
    echo ❌ O programa encontrou um erro
    echo.
    echo 💡 VERIFICAÇÕES:
    echo - Arquivo CNPJ.xlsx existe e está correto?
    echo - Conexão com internet está funcionando?
    echo - Antivírus não está bloqueando?
    echo.
)

echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0

REM ==================================================
REM TRATAMENTO DE ERROS
REM ==================================================
:install_error
echo.
echo ====================================================
echo                ERRO NA INSTALAÇÃO
echo ====================================================
echo.
echo ❌ Não foi possível instalar as bibliotecas necessárias
echo.
echo 💡 SOLUÇÕES:
echo.
echo 1. EXECUTE COMO ADMINISTRADOR:
echo    - Clique direito neste arquivo
echo    - Escolha "Executar como administrador"
echo.
echo 2. INSTALE VISUAL STUDIO BUILD TOOLS (para Python 3.13+):
echo    - Acesse: https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo    - Baixe e instale "Build Tools for Visual Studio"
echo    - Selecione "C++ build tools"
echo.
echo 3. USE PYTHON MAIS ANTIGO:
echo    - Desinstale Python atual
echo    - Instale Python 3.11 ou 3.12 de python.org
echo    - Execute este script novamente
echo.
echo 4. VERIFIQUE CONEXÃO:
echo    - Certifique-se que tem internet
echo    - Desabilite antivírus temporariamente
echo.
echo 5. INSTALAÇÃO MANUAL:
echo    - Abra Prompt de Comando como Administrador
echo    - Digite: pip install pandas requests openpyxl
echo.
pause
exit /b 1