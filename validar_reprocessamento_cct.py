import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config_banco import obter_caminho_banco
from processar_pdf import extrair_dados_com_gemini, salvar_cct_no_banco

ARQUIVO = r"c:/Users/marce/Desktop/Automacao_Gestao_Sindical/documentos_sindicais/Processados/2025_2026_ SHESSMAR_MARINGA_FARMACEUTICOS_CONVENCAO.pdf"

print("PDF:", os.path.basename(ARQUIVO), flush=True)
dados = extrair_dados_com_gemini(ARQUIVO)
print("CHAVES_EXTRAIDAS:", sorted(dados.keys()), flush=True)
print("REAJUSTE_EXTRAIDO:", dados.get("reajuste_salarial"), flush=True)
print("VALE_REFEICAO_EXTRAIDO:", dados.get("vale_refeicao"), flush=True)
print("AUXILIO_CRECHE_EXTRAIDO:", dados.get("auxilio_creche"), flush=True)

dados["arquivo_origem"] = os.path.basename(ARQUIVO)
salvar_cct_no_banco(dados)

conn = sqlite3.connect(obter_caminho_banco())
cur = conn.cursor()
row = cur.execute(
    "SELECT dados_completos FROM ccts WHERE arquivo_origem = ? ORDER BY id DESC LIMIT 1",
    (os.path.basename(ARQUIVO),),
).fetchone()
payload = json.loads(row[0]) if row and row[0] else {}
print("NO_BANCO_REAJUSTE:", payload.get("reajuste_salarial"), flush=True)
print("NO_BANCO_VALE_REFEICAO:", payload.get("vale_refeicao"), flush=True)
print("NO_BANCO_AUXILIO_CRECHE:", payload.get("auxilio_creche"), flush=True)
conn.close()
