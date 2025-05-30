#!/bin/bash

echo "===================================================="
echo "           CONSULTA DE CNPJ EM MASSA"
echo "===================================================="
echo

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Iniciando programa..."
echo
python3 consulta_cnpj.py

echo
echo "Programa finalizado."
echo "Pressione Enter para fechar..."
read