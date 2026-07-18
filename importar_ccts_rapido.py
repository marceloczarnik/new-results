import os
import sqlite3
import json
import re
from datetime import datetime
from config_banco import obter_caminho_banco
from core.painel_helpers import resolver_entidades_cct, inferir_abrangencia_cct, inferir_titulo_cct

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = obter_caminho_banco()
PASTA_PROCESSADOS = os.path.join(BASE_DIR, "documentos_sindicais", "Processados")
PASTA_NOVOS = os.path.join(BASE_DIR, "documentos_sindicais", "Novos")

def extrair_dados_do_nome(nome_arquivo):
    """Extrai dados básicos do nome do arquivo PDF."""
    # Remove extensão
    nome = nome_arquivo.replace(".pdf", "").replace("_", " ")
    
    # Extrai vigência (ex: 2025_2026 -> 2025-2026)
    vigencia_match = re.match(r"(\d{4})[\s_](\d{4})", nome)
    vigencia_inicio = vigencia_match.group(1) if vigencia_match else "2025"
    vigencia_fim = vigencia_match.group(2) if vigencia_match else "2026"
    
    patronal, laboral = resolver_entidades_cct("Patronal", "Laboral", nome_arquivo)
    abrangencia = inferir_abrangencia_cct(nome_arquivo, "Paraná")
    titulo = inferir_titulo_cct(nome_arquivo, vigencia_inicio, vigencia_fim)
    
    return {
        "arquivo_origem": nome_arquivo,
        "vigencia_inicio": vigencia_inicio,
        "vigencia_fim": vigencia_fim,
        "id_entidade_patronal": patronal or "Não Identificado",
        "id_entidade_sindical": laboral or "Não Identificado",
        "abrangencia_territorial": abrangencia,
        "titulo": titulo,
        "piso_salarial": "A definir",
        "clausula_critica": "Cláusula a ser extraída",
    }

def salvar_cct_no_banco(dados):
    """Salva CCT no banco."""
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(ccts)")
        colunas_existentes = {c[1] for c in cursor.fetchall()}

        payload = {
            "arquivo_origem": dados["arquivo_origem"],
            "id_entidade_patronal": dados["id_entidade_patronal"],
            "id_entidade_sindical": dados["id_entidade_sindical"],
            "vigencia_inicio": dados["vigencia_inicio"],
            "vigencia_fim": dados["vigencia_fim"],
            "abrangencia_territorial": dados["abrangencia_territorial"],
            "titulo": dados["titulo"],
            "piso_salarial": dados["piso_salarial"],
            "clausula_critica": dados["clausula_critica"],
            "dados_completos": json.dumps(dados, ensure_ascii=False),
        }

        if "categoria_profissional" in colunas_existentes:
            payload["categoria_profissional"] = dados.get("categoria_profissional") or "Categoria a definir"
        if "status_validacao" in colunas_existentes:
            payload["status_validacao"] = dados.get("status_validacao") or "PENDENTE"
        if "data_cadastro" in colunas_existentes:
            payload["data_cadastro"] = dados.get("data_cadastro") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Como arquivo_origem não é UNIQUE no schema atual, removemos o registro anterior
        # para garantir comportamento de reimportação (upsert por arquivo).
        if "arquivo_origem" in colunas_existentes:
            cursor.execute("DELETE FROM ccts WHERE arquivo_origem = ?", (dados["arquivo_origem"],))

        colunas_insert = [c for c in payload.keys() if c in colunas_existentes]
        valores_insert = [payload[c] for c in colunas_insert]
        placeholders = ", ".join(["?"] * len(colunas_insert))

        cursor.execute(
            f"INSERT INTO ccts ({', '.join(colunas_insert)}) VALUES ({placeholders})",
            valores_insert,
        )
        conn.commit()
        print(f"✅ {dados['arquivo_origem']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar {dados['arquivo_origem']}: {e}")
        return False
    finally:
        conn.close()

def importar_arquivos():
    """Importa todos os arquivos de ambas as pastas."""
    total_importados = 0
    
    # Cria tabela se não existir
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ccts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_origem TEXT UNIQUE,
            id_entidade_patronal TEXT,
            id_entidade_sindical TEXT,
            vigencia_inicio TEXT,
            vigencia_fim TEXT,
            abrangencia_territorial TEXT,
            titulo TEXT,
            piso_salarial TEXT,
            clausula_critica TEXT,
            dados_completos TEXT
        )
    """)
    conn.close()
    
    # Importa de Processados
    print(f"\n📁 Importando arquivos de Processados...")
    if os.path.exists(PASTA_PROCESSADOS):
        arquivos = [f for f in os.listdir(PASTA_PROCESSADOS) if f.endswith('.pdf')]
        for arquivo in arquivos:
            dados = extrair_dados_do_nome(arquivo)
            if salvar_cct_no_banco(dados):
                total_importados += 1
    
    # Importa de Novos
    print(f"\n📁 Importando arquivos de Novos...")
    if os.path.exists(PASTA_NOVOS):
        arquivos = [f for f in os.listdir(PASTA_NOVOS) if f.endswith('.pdf')]
        for arquivo in arquivos:
            dados = extrair_dados_do_nome(arquivo)
            if salvar_cct_no_banco(dados):
                total_importados += 1
    
    # Verifica total no banco
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ccts")
    total_banco = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ IMPORTAÇÃO CONCLUÍDA")
    print(f"📊 Total importado: {total_importados} arquivos")
    print(f"📊 Total no banco: {total_banco} CCTs")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("🚀 Iniciando importação rápida de CCTs...")
    importar_arquivos()
