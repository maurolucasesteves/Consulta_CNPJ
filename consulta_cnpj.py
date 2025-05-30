# consulta_cnpj.py
# CONSULTA DE CNPJ EM MASSA - VERSÃO LOCAL
# ========================================

import pandas as pd
import requests
import time
import json
import os
from datetime import datetime
import random
from pathlib import Path

# CONFIGURAÇÕES
# =============
ARQUIVO_ENTRADA = "CNPJ.xlsx"              # Coloque seu arquivo na mesma pasta
COLUNA_CNPJ = "CNPJ"                       # Nome da coluna com os CNPJs
ARQUIVO_SAIDA = "resultado_cnpj.xlsx"      # Arquivo onde salvará os resultados
LOTE_SIZE = 25                             # CNPJs por lote (para salvar progresso)
REMOVER_DUPLICADOS = True                  # Remove CNPJs duplicados
TEMPO_PAUSA_MIN = 18                       # Tempo mínimo entre consultas (segundos)
TEMPO_PAUSA_MAX = 22                       # Tempo máximo entre consultas (segundos)

def limpar_cnpj(cnpj):
    """Remove caracteres não numéricos do CNPJ"""
    if pd.isna(cnpj):
        return None
    return ''.join(filter(str.isdigit, str(cnpj)))

def consultar_receita_ws(cnpj):
    """Consulta dados na ReceitaWS (API gratuita)"""
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se há erro na resposta
            if dados.get('status') == 'ERROR':
                return {'erro': dados.get('message', 'Erro desconhecido')}
            
            # Monta endereço completo
            endereco_partes = [
                dados.get('logradouro', ''),
                dados.get('numero', ''),
                dados.get('complemento', '')
            ]
            endereco_completo = ' '.join(filter(None, endereco_partes))
            
            return {
                'razao_social': dados.get('nome', ''),
                'nome_fantasia': dados.get('fantasia', ''),
                'telefone': dados.get('telefone', ''),
                'email': dados.get('email', ''),
                'endereco': endereco_completo.strip(),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cep': dados.get('cep', ''),
                'situacao': dados.get('situacao', ''),
                'atividade_principal': dados.get('atividade_principal', [{}])[0].get('text', '') if dados.get('atividade_principal') else '',
                'capital_social': dados.get('capital_social', ''),
                'data_abertura': dados.get('abertura', ''),
                'natureza_juridica': dados.get('natureza_juridica', ''),
                'porte': dados.get('porte', ''),
                'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fonte': 'ReceitaWS'
            }
        
        elif response.status_code == 429:
            return {'erro': 'Limite de consultas excedido'}
        else:
            return {'erro': f'Erro HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'erro': 'Timeout na consulta'}
    except requests.exceptions.RequestException as e:
        return {'erro': f'Erro de conexão: {str(e)}'}
    except Exception as e:
        return {'erro': f'Erro inesperado: {str(e)}'}

def consultar_brasil_api(cnpj):
    """Consulta dados na BrasilAPI (API alternativa gratuita)"""
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Monta endereço completo
            endereco_partes = [
                dados.get('descricao_tipo_de_logradouro', ''),
                dados.get('logradouro', ''),
                dados.get('numero', ''),
                dados.get('complemento', '')
            ]
            endereco_completo = ' '.join(filter(None, endereco_partes))
            
            return {
                'razao_social': dados.get('razao_social', ''),
                'nome_fantasia': dados.get('nome_fantasia', ''),
                'telefone': dados.get('ddd_telefone_1', ''),
                'email': dados.get('correio_eletronico', ''),
                'endereco': endereco_completo.strip(),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cep': dados.get('cep', ''),
                'situacao': dados.get('descricao_situacao_cadastral', ''),
                'atividade_principal': dados.get('cnae_fiscal_descricao', ''),
                'capital_social': str(dados.get('capital_social', '')),
                'data_abertura': dados.get('data_inicio_atividade', ''),
                'natureza_juridica': dados.get('descricao_natureza_juridica', ''),
                'porte': dados.get('descricao_porte', ''),
                'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fonte': 'BrasilAPI'
            }
        else:
            return {'erro': f'Erro HTTP {response.status_code}'}
            
    except Exception as e:
        return {'erro': f'Erro na BrasilAPI: {str(e)}'}

def consultar_cnpj_multiplas_fontes(cnpj):
    """Tenta consultar em múltiplas APIs"""
    
    # Primeiro tenta ReceitaWS
    resultado = consultar_receita_ws(cnpj)
    
    # Se deu erro, tenta BrasilAPI
    if 'erro' in resultado:
        print(f"    ReceitaWS falhou, tentando BrasilAPI...")
        time.sleep(2)
        resultado = consultar_brasil_api(cnpj)
    
    return resultado

def verificar_arquivos():
    """Verifica se os arquivos necessários existem"""
    
    print("🔍 VERIFICANDO ARQUIVOS...")
    print("=" * 40)
    
    # Verifica arquivo de entrada
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"❌ Arquivo não encontrado: {ARQUIVO_ENTRADA}")
        print(f"📁 Coloque o arquivo {ARQUIVO_ENTRADA} na mesma pasta que este script")
        print(f"📂 Pasta atual: {os.getcwd()}")
        return False
    else:
        print(f"✅ Arquivo encontrado: {ARQUIVO_ENTRADA}")
    
    # Verifica se consegue ler o arquivo
    try:
        df = pd.read_excel(ARQUIVO_ENTRADA)
        print(f"✅ Arquivo lido com sucesso: {len(df)} linhas")
        
        # Verifica se a coluna existe
        if COLUNA_CNPJ not in df.columns:
            print(f"❌ Coluna '{COLUNA_CNPJ}' não encontrada!")
            print(f"📋 Colunas disponíveis: {list(df.columns)}")
            return False
        else:
            print(f"✅ Coluna '{COLUNA_CNPJ}' encontrada")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False

def testar_conexao_apis():
    """Testa se as APIs estão funcionando"""
    
    print("\n🌐 TESTANDO CONEXÃO COM APIs...")
    print("=" * 40)
    
    # CNPJ de teste (Magazine Luiza)
    cnpj_teste = "47960950000121"
    
    # Testa ReceitaWS
    print("🔄 Testando ReceitaWS...")
    resultado_receita = consultar_receita_ws(cnpj_teste)
    
    if 'erro' not in resultado_receita:
        print("✅ ReceitaWS funcionando!")
        print(f"   Empresa teste: {resultado_receita.get('razao_social', 'N/A')}")
    else:
        print(f"❌ ReceitaWS com problema: {resultado_receita['erro']}")
    
    time.sleep(3)  # Pausa entre testes
    
    # Testa BrasilAPI
    print("🔄 Testando BrasilAPI...")
    resultado_brasil = consultar_brasil_api(cnpj_teste)
    
    if 'erro' not in resultado_brasil:
        print("✅ BrasilAPI funcionando!")
        print(f"   Empresa teste: {resultado_brasil.get('razao_social', 'N/A')}")
    else:
        print(f"❌ BrasilAPI com problema: {resultado_brasil['erro']}")
    
    # Verifica se pelo menos uma API funciona
    if 'erro' not in resultado_receita or 'erro' not in resultado_brasil:
        print("\n🎉 Pelo menos uma API está funcionando! Pode prosseguir.")
        return True
    else:
        print("\n⚠️  Ambas as APIs estão com problemas. Tente mais tarde.")
        return False

def testar_consulta_usuario(quantidade=3):
    """Testa a consulta com CNPJs do usuário"""
    
    print(f"\n🧪 TESTANDO COM SEUS CNPJs...")
    print("=" * 40)
    
    # Carrega os dados
    df = pd.read_excel(ARQUIVO_ENTRADA)
    df['cnpj_limpo'] = df[COLUNA_CNPJ].apply(limpar_cnpj)
    df_validos = df[df['cnpj_limpo'].notna() & (df['cnpj_limpo'].str.len() == 14)].copy()
    
    if REMOVER_DUPLICADOS:
        df_validos = df_validos.drop_duplicates(subset=['cnpj_limpo'])
    
    if len(df_validos) == 0:
        print("❌ Nenhum CNPJ válido encontrado!")
        return False
    
    # Pega amostra para teste
    cnpjs_teste = df_validos.head(quantidade)
    print(f"📊 Testando com {len(cnpjs_teste)} CNPJs do seu arquivo...")
    
    sucessos = 0
    erros = 0
    
    for i, (_, row) in enumerate(cnpjs_teste.iterrows()):
        cnpj_original = row[COLUNA_CNPJ]
        cnpj_limpo = row['cnpj_limpo']
        
        print(f"\n{i+1}. 🔍 Consultando: {cnpj_original}")
        
        resultado = consultar_cnpj_multiplas_fontes(cnpj_limpo)
        
        if 'erro' not in resultado:
            sucessos += 1
            print(f"   ✅ Sucesso!")
            print(f"   📊 {resultado.get('razao_social', 'N/A')}")
            print(f"   📞 {resultado.get('telefone', 'Sem telefone')}")
            print(f"   📍 {resultado.get('cidade', 'N/A')}/{resultado.get('uf', 'N/A')}")
        else:
            erros += 1
            print(f"   ❌ Erro: {resultado['erro']}")
        
        # Pausa entre consultas (exceto na última)
        if i < len(cnpjs_teste) - 1:
            pausa = random.uniform(TEMPO_PAUSA_MIN, TEMPO_PAUSA_MAX)
            print(f"   ⏳ Aguardando {pausa:.1f} segundos...")
            time.sleep(pausa)
    
    # Estatísticas
    print(f"\n📊 RESULTADO DO TESTE:")
    print(f"✅ Sucessos: {sucessos}/{quantidade} ({sucessos/quantidade*100:.1f}%)")
    print(f"❌ Erros: {erros}/{quantidade} ({erros/quantidade*100:.1f}%)")
    
    if sucessos > 0:
        print("\n🎉 Teste bem-sucedido! APIs funcionando com seus dados.")
        return True
    else:
        print("\n⚠️  Teste falhou. Verifique sua conexão ou tente mais tarde.")
        return False

def processar_todos_cnpjs():
    """Processa todos os CNPJs"""
    
    print(f"\n🚀 PROCESSAMENTO COMPLETO")
    print("=" * 40)
    
    # Carrega e prepara dados
    df = pd.read_excel(ARQUIVO_ENTRADA)
    print(f"📊 Arquivo carregado: {len(df)} linhas")
    
    # Limpa CNPJs
    df['cnpj_limpo'] = df[COLUNA_CNPJ].apply(limpar_cnpj)
    df_validos = df[df['cnpj_limpo'].notna() & (df['cnpj_limpo'].str.len() == 14)].copy()
    print(f"🧹 CNPJs válidos: {len(df_validos)}")
    
    # Remove duplicados
    if REMOVER_DUPLICADOS:
        tamanho_original = len(df_validos)
        df_validos = df_validos.drop_duplicates(subset=['cnpj_limpo'])
        duplicados = tamanho_original - len(df_validos)
        if duplicados > 0:
            print(f"🔄 Duplicados removidos: {duplicados}")
        print(f"📊 CNPJs únicos: {len(df_validos)}")
    
    # Verifica se há CNPJs já processados
    resultados_existentes = []
    cnpjs_processados = set()
    
    if os.path.exists(ARQUIVO_SAIDA):
        try:
            df_existente = pd.read_excel(ARQUIVO_SAIDA)
            resultados_existentes = df_existente.to_dict('records')
            cnpjs_processados = set(df_existente['cnpj_limpo'].astype(str))
            print(f"📄 Arquivo de saída existe: {len(cnpjs_processados)} CNPJs já processados")
        except:
            print("⚠️  Erro ao carregar arquivo existente. Recomeçando...")
    
    # Filtra CNPJs pendentes
    df_pendentes = df_validos[~df_validos['cnpj_limpo'].astype(str).isin(cnpjs_processados)].copy()
    
    if len(df_pendentes) == 0:
        print("✅ Todos os CNPJs já foram processados!")
        return
    
    print(f"📋 CNPJs pendentes: {len(df_pendentes)}")
    
    # Estimativa de tempo
    tempo_estimado_min = len(df_pendentes) * (TEMPO_PAUSA_MIN + TEMPO_PAUSA_MAX) / 2 / 60
    print(f"⏱️  Tempo estimado: {tempo_estimado_min:.1f} minutos")
    
    # Confirma antes de começar
    resposta = input(f"\n❓ Processar {len(df_pendentes)} CNPJs? (s/n): ").lower().strip()
    if resposta != 's':
        print("❌ Processamento cancelado.")
        return
    
    # Processamento
    print(f"\n🔄 Iniciando processamento...")
    
    contador = 0
    sucessos = 0
    erros = 0
    
    try:
        for index, row in df_pendentes.iterrows():
            contador += 1
            cnpj_original = row[COLUNA_CNPJ]
            cnpj_limpo = row['cnpj_limpo']
            
            print(f"\n[{contador}/{len(df_pendentes)}] 🔍 {cnpj_original}")
            
            # Faz a consulta
            resultado = consultar_cnpj_multiplas_fontes(cnpj_limpo)
            
            # Adiciona informações extras
            resultado['cnpj_original'] = cnpj_original
            resultado['cnpj_limpo'] = cnpj_limpo
            resultado['linha_original'] = index + 1
            
            # Adiciona dados originais da planilha
            for col in df.columns:
                if col != COLUNA_CNPJ and col != 'cnpj_limpo':
                    resultado[f'original_{col}'] = row.get(col, '')
            
            resultados_existentes.append(resultado)
            
            if 'erro' not in resultado:
                sucessos += 1
                print(f"    ✅ {resultado.get('razao_social', 'N/A')}")
            else:
                erros += 1
                print(f"    ❌ {resultado['erro']}")
            
            # Mostra progresso
            print(f"    📊 Sucessos: {sucessos} | Erros: {erros} | Taxa: {sucessos/(sucessos+erros)*100:.1f}%")
            
            # Salva progresso a cada lote
            if contador % LOTE_SIZE == 0:
                df_resultado = pd.DataFrame(resultados_existentes)
                df_resultado.to_excel(ARQUIVO_SAIDA, index=False)
                print(f"    💾 Progresso salvo (lote {contador//LOTE_SIZE})")
            
            # Pausa entre consultas (exceto na última)
            if contador < len(df_pendentes):
                pausa = random.uniform(TEMPO_PAUSA_MIN, TEMPO_PAUSA_MAX)
                print(f"    ⏳ Pausando {pausa:.1f}s...")
                time.sleep(pausa)
    
    except KeyboardInterrupt:
        print("\n⚠️  Processamento interrompido pelo usuário!")
        print("💾 Salvando progresso atual...")
    
    except Exception as e:
        print(f"\n❌ Erro durante processamento: {e}")
        print("💾 Salvando progresso atual...")
    
    # Salva resultado final
    print(f"\n💾 Salvando resultado final...")
    df_resultado = pd.DataFrame(resultados_existentes)
    df_resultado.to_excel(ARQUIVO_SAIDA, index=False)
    
    # Estatísticas finais
    print(f"\n📊 PROCESSAMENTO CONCLUÍDO!")
    print(f"✅ Total processado: {contador}")
    print(f"✅ Sucessos: {sucessos} ({sucessos/contador*100:.1f}%)")
    print(f"❌ Erros: {erros} ({erros/contador*100:.1f}%)")
    print(f"💾 Resultado salvo em: {ARQUIVO_SAIDA}")

def analisar_resultados():
    """Analisa os resultados obtidos"""
    
    if not os.path.exists(ARQUIVO_SAIDA):
        print(f"❌ Arquivo de resultados não encontrado: {ARQUIVO_SAIDA}")
        return
    
    try:
        df = pd.read_excel(ARQUIVO_SAIDA)
        
        print("📊 ANÁLISE DOS RESULTADOS")
        print("=" * 50)
        print(f"Total de registros: {len(df)}")
        
        # Sucessos vs Erros
        erros = df['erro'].notna().sum()
        sucessos = len(df) - erros
        print(f"✅ Sucessos: {sucessos} ({sucessos/len(df)*100:.1f}%)")
        print(f"❌ Erros: {erros} ({erros/len(df)*100:.1f}%)")
        
        if sucessos > 0:
            df_sucessos = df[df['erro'].isna()]
            
            # Dados de contato
            com_telefone = df_sucessos['telefone'].notna().sum()
            com_email = df_sucessos['email'].notna().sum()
            com_endereco = df_sucessos['endereco'].notna().sum()
            
            print(f"\n📞 Com telefone: {com_telefone} ({com_telefone/sucessos*100:.1f}%)")
            print(f"📧 Com email: {com_email} ({com_email/sucessos*100:.1f}%)")
            print(f"📍 Com endereço: {com_endereco} ({com_endereco/sucessos*100:.1f}%)")
            
            # Top UFs
            print(f"\n🗺️  Top 10 UFs:")
            top_ufs = df_sucessos['uf'].value_counts().head(10)
            for uf, count in top_ufs.items():
                print(f"   {uf}: {count} empresas")
            
            # Situação cadastral
            print(f"\n📋 Situação Cadastral:")
            situacoes = df_sucessos['situacao'].value_counts().head(5)
            for situacao, count in situacoes.items():
                print(f"   {situacao}: {count}")
        
        # Top erros
        if erros > 0:
            print(f"\n❌ Top 5 tipos de erro:")
            top_erros = df[df['erro'].notna()]['erro'].value_counts().head(5)
            for erro, count in top_erros.items():
                print(f"   {erro}: {count}")
        
    except Exception as e:
        print(f"❌ Erro ao analisar resultados: {e}")

def menu_principal():
    """Menu principal do programa"""
    
    print("🏢 CONSULTA DE CNPJ EM MASSA")
    print("=" * 50)
    print("📂 Arquivo de entrada:", ARQUIVO_ENTRADA)
    print("📝 Arquivo de saída:", ARQUIVO_SAIDA)
    print("🔄 Remover duplicados:", "Sim" if REMOVER_DUPLICADOS else "Não")
    print("⏱️  Pausa entre consultas:", f"{TEMPO_PAUSA_MIN}-{TEMPO_PAUSA_MAX}s")
    
    while True:
        print(f"\n📋 OPÇÕES:")
        print("1. 🔍 Verificar arquivos")
        print("2. 🌐 Testar conexão com APIs")
        print("3. 🧪 Testar com seus CNPJs (3 amostras)")
        print("4. 🚀 Processar todos os CNPJs")
        print("5. 📊 Analisar resultados")
        print("6. ❌ Sair")
        
        try:
            opcao = input("\n❓ Escolha uma opção (1-6): ").strip()
            
            if opcao == '1':
                verificar_arquivos()
            
            elif opcao == '2':
                testar_conexao_apis()
            
            elif opcao == '3':
                if verificar_arquivos():
                    testar_consulta_usuario()
                
            elif opcao == '4':
                if verificar_arquivos():
                    processar_todos_cnpjs()
            
            elif opcao == '5':
                analisar_resultados()
            
            elif opcao == '6':
                print("👋 Até logo!")
                break
            
            else:
                print("❌ Opção inválida!")
                
        except KeyboardInterrupt:
            print("\n👋 Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    menu_principal()