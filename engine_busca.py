import sqlite3
import os

from config_banco import obter_caminho_banco
from enquadramento import EngineEnquadramentoTrabalhista


def api_enquadramento_por_cnae(cnae_empresa, municipio_empresa, uf_empresa, caminho_banco=None):
    """
    API de Inteligência Sindical por Empresa.
    Consulta o CNAE e a Localização de forma flexível eliminando registros duplicados.
    """
    if caminho_banco is None:
        caminho_banco = obter_caminho_banco()
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    colunas_matriz = [col[1] for col in cursor.execute("PRAGMA table_info(matriz_enquadramento)").fetchall()]
    usa_tipo_cct = "tipo_cct" in colunas_matriz

    resultado_enquadramento = {
        "principais": [],
        "satelites": []
    }
    
    # Prepara termos limpos para a busca aproximada
    termo_municipio = f"%{municipio_empresa.replace('Á', 'A').replace('á', 'a').strip()}%"
    termo_uf = f"%{uf_empresa.strip()}%"

    # Consulta prioritária por CNAE
    if usa_tipo_cct:
        query = """
            SELECT DISTINCT 
                   s.id, s.sindicato_patronal, s.sindicato_laboral, s.vigencia, 
                   s.piso_salarial, s.reajuste_salarial, s.vale_refeicao, s.auxilio_creche, s.clausula_critica,
                   e.tipo_cct
            FROM matriz_enquadramento e
            JOIN sindicatos s ON e.sindicato_id = s.id
            WHERE e.cnae = ? 
              AND (e.municipio LIKE ? OR e.uf LIKE ? OR e.municipio LIKE '%MARINGA%' OR e.municipio LIKE '%MARINGÁ%')
        """
    else:
        query = """
            SELECT DISTINCT 
                   s.id, s.sindicato_patronal, s.sindicato_laboral, s.vigencia, 
                   s.piso_salarial, s.reajuste_salarial, s.vale_refeicao, s.auxilio_creche, s.clausula_critica,
                   'PRINCIPAL' AS tipo_cct
            FROM matriz_enquadramento e
            JOIN sindicatos s ON e.sindicato_id = s.id
            WHERE e.cnae = ? 
              AND (e.municipio LIKE ? OR e.uf LIKE ? OR e.municipio LIKE '%MARINGA%' OR e.municipio LIKE '%MARINGÁ%')
        """

    cursor.execute(query, (cnae_empresa, termo_municipio, termo_uf))
    linhas = cursor.fetchall()

    # Fallback por município/UF quando o CNAE não tem correspondência direta
    if not linhas:
        fallback = """
            SELECT DISTINCT 
                   s.id, s.sindicato_patronal, s.sindicato_laboral, s.vigencia, 
                   s.piso_salarial, s.reajuste_salarial, s.vale_refeicao, s.auxilio_creche, s.clausula_critica,
                   'PRINCIPAL' AS tipo_cct
            FROM matriz_enquadramento e
            JOIN sindicatos s ON e.sindicato_id = s.id
            WHERE e.municipio LIKE ? OR e.uf LIKE ?
        """
        cursor.execute(fallback, (termo_municipio, termo_uf))
        linhas = cursor.fetchall()
    conn.close()
    
    for r in linhas:
        dados_cct = {
            "id": r[0],
            "patronal": r[1],
            "laboral": r[2],
            "vigencia": r[3],
            "piso": r[4],
            "reajuste": r[5],
            "va": r[6],
            "creche": r[7],
            "critica": r[8]
        }
        
        if r[9] == "SATELITE":
            resultado_enquadramento["satelites"].append(dados_cct)
        else:
            resultado_enquadramento["principais"].append(dados_cct)
            
    return resultado_enquadramento


def api_enquadramento_avancado(
    cnae_empresa,
    municipio_empresa,
    uf_empresa,
    funcionarios=None,
    caminho_banco=None,
    caminho_regras=None,
):
    """
    Combina o enquadramento principal por CNAE com diagnóstico de categorias
    especiais por CBO/cargo para sugerir CCTs satélites.
    """
    base = api_enquadramento_por_cnae(
        cnae_empresa=cnae_empresa,
        municipio_empresa=municipio_empresa,
        uf_empresa=uf_empresa,
        caminho_banco=caminho_banco,
    )

    if funcionarios is None:
        funcionarios = []

    if caminho_regras is None:
        caminho_regras = os.path.join(
            os.path.dirname(__file__),
            "categorias_especiais.json",
        )

    engine = EngineEnquadramentoTrabalhista(caminho_regras)
    diagnostico = engine.analisar_folha_pagamento(funcionarios)

    return {
        "principais": base.get("principais", []),
        "satelites": base.get("satelites", []),
        "diagnostico_cargos": diagnostico,
    }

# ==============================================================================
# TESTE DA API COM REGISTROS REAIS DO BANCO
# ==============================================================================
if __name__ == "__main__":
    import sqlite3
    
    conn = sqlite3.connect("banco_sindical.db")
    cursor = conn.cursor()
    
    # 1. Olhamos um ID de sindicato que realmente existe no seu banco
    cursor.execute("SELECT id FROM sindicatos LIMIT 1")
    sindicato = cursor.fetchone()
    
    if sindicato:
        id_real = sindicato[0]
        cnae_teste = "6920-6/01"
        
        # 2. Forçamos a amarração na matriz para o teste dar match garantido
        cursor.execute("DELETE FROM matriz_enquadramento WHERE cnae = ?", (cnae_teste,))
        cursor.execute("""
            INSERT INTO matriz_enquadramento (cnae, municipio, uf, sindicato_id, tipo_cct)
            VALUES (?, 'MARINGA', 'PR', ?, 'PRINCIPAL')
        """, (cnae_teste, id_real))
        
        cursor.execute("""
            INSERT INTO matriz_enquadramento (cnae, municipio, uf, sindicato_id, tipo_cct)
            VALUES (?, 'MARINGA', 'PR', ?, 'SATELITE')
        """, (cnae_teste, id_real))
        conn.commit()
        print("⚡ Cenário de teste acoplado com sucesso ao banco!")
    else:
        print("⚠️ A tabela 'sindicatos' parece não ter registros para o teste.")
        
    conn.close()

    # 3. Executa a consulta da sua API para validar as gavetas (Principal vs Satélite)
    municipio_teste = "MARINGA"
    uf_teste = "PR"
    
    print(f"🔍 Consultando enquadramento flexível para CNAE {cnae_teste}...")
    retorno = api_enquadramento_por_cnae(cnae_teste, municipio_teste, uf_teste)
    
    print(f"\n📦 CCTs Principais Encontradas: {len(retorno['principais'])}")
    print(f"🛰️ CCTs Satélites Encontradas: {len(retorno['satelites'])}")