#!/bin/bash

echo "===================================================="
echo "     INSTALACAO AUTOMATICA - CONSULTA CNPJ"
echo "===================================================="
echo

echo "[1/5] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    echo "Por favor, instale Python 3.8+ usando:"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "macOS: brew install python3"
    exit 1
fi
echo "✓ Python encontrado!"

echo
echo "[2/5] Criando ambiente virtual..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao criar ambiente virtual!"
    exit 1
fi
echo "✓ Ambiente virtual criado!"

echo
echo "[3/5] Ativando ambiente virtual..."
source venv/bin/activate
echo "✓ Ambiente virtual ativado!"

echo
echo "[4/5] Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências!"
    exit 1
fi
echo "✓ Dependências instaladas!"

echo
echo "[5/5] Configuração concluída!"
echo
echo "===================================================="
echo "               INSTALAÇÃO CONCLUÍDA!"
echo "===================================================="
echo
echo "PRÓXIMOS PASSOS:"
echo "1. Coloque seu arquivo CNPJ.xlsx nesta pasta"
echo "2. Execute: ./executar.sh"
echo
echo "Pressione Enter para continuar..."
read