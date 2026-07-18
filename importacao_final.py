import os
import sqlite3
import json
import re
from core.painel_helpers import resolver_entidades_cct, inferir_abrangencia_cct, inferir_titulo_cct

BASE_DIR = os.getcwd()
CAMINHO_BANCO = os.path.join(BASE_DIR, 'dados', 'dados_sindicais.db')
PASTA_PROCESSADOS = os.path.join(BASE_DIR, "documentos_sindicais", "Processados")
PASTA_NOVOS = os.path.join(BASE_DIR, "documentos_sindicais", "Novos")

def extrair_dados_do_nome(nome_arquivo):
    nome = nome_arquivo.replace(".pdf", "").replace("_", " ")
    vigencia_match = re.match(r"(\d{4})[\s_](\d{4})", nome)
    vigencia_inicio = vigencia_match.group(1) if vigencia_match else "2025"
    vigencia_fim = vigencia_match.group(2) if vigencia_match else "2026"
    patronal, laboral = resolver_entidades_cct("Patronal", "Laboral", nome_arquivo)
    
    return {
        "arquivo_origem": nome_arquivo,
        "vigencia_inicio": vigencia_inicio,
        "vigencia_fim": vigencia_fim,
        "id_entidade_patronal": patronal,
        "id_entidade_sindical": laboral,
        "abrangencia_territorial": inferir_abrangencia_cct(nome_arquivo, "Paraná"),
        "titulo": inferir_titulo_cct(nome_arquivo, vigencia_inicio, vigencia_fim),
        "piso_salarial": "A definir",
        "clausula_critica": "",
    }

def salvar_no_banco(dados):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO ccts (
                arquivo_origem, id_entidade_patronal, id_entidade_sindical, 
                vigencia_inicio, vigencia_fim, abrangencia_territorial, titulo, 
                piso_salarial, clausula_critica, dados_completos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados["arquivo_origem"], dados["id_entidade_patronal"], dados["id_entidade_sindical"],
            dados["vigencia_inicio"], dados["vigencia_fim"], dados["abrangencia_territorial"],
            dados["titulo"], dados["piso_salarial"], dados["clausula_critica"],
            json.dumps(dados, ensure_ascii=False)
        ))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

total = 0

# Processados
if os.path.exists(PASTA_PROCESSADOS):
    for arquivo in os.listdir(PASTA_PROCESSADOS):
        if arquivo.endswith('.pdf'):
            if salvar_no_banco(extrair_dados_do_nome(arquivo)):
                total += 1

# Novos
if os.path.exists(PASTA_NOVOS):
    for arquivo in os.listdir(PASTA_NOVOS):
        if arquivo.endswith('.pdf'):
            if salvar_no_banco(extrair_dados_do_nome(arquivo)):
                total += 1

# Verifica
conn = sqlite3.connect(CAMINHO_BANCO)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM ccts")
total_banco = cursor.fetchone()[0]
conn.close()

print(f"Importacao concluida: {total_banco} CCTs no banco")
