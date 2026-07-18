import json
import os
import sqlite3
import sys
import time
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from processar_pdf import PASTA_PROCESSADOS, CAMINHO_BANCO, extrair_dados_com_gemini, salvar_cct_no_banco

PASTA_NOVOS = os.path.join(BASE_DIR, "documentos_sindicais", "Novos")

ALVOS = {
    "reajuste_salarial": ["reajuste_salarial", "reajuste", "percentual_reajuste", "indice_reajuste"],
    "vale_refeicao": ["vale_refeicao", "vale_alimentacao", "vr", "va"],
    "auxilio_creche": ["auxilio_creche", "creche", "beneficio_creche"],
}


def carregar_ccts():
    conn = sqlite3.connect(CAMINHO_BANCO)
    cur = conn.cursor()
    rows = cur.execute("SELECT arquivo_origem, dados_completos FROM ccts ORDER BY arquivo_origem").fetchall()
    conn.close()
    return rows


def parse_json(seguro):
    if isinstance(seguro, str) and seguro.strip():
        try:
            dado = json.loads(seguro)
            if isinstance(dado, dict):
                return dado
        except Exception:
            pass
    return {}


def valor_de_campo(dados, aliases):
    for alias in aliases:
        if alias in dados:
            valor = dados.get(alias)
            if valor is not None and str(valor).strip() != "":
                return str(valor).strip()
            return ""
    return ""


def pendencias_por_arquivo(rows):
    pendencias = []
    for arquivo, dados_raw in rows:
        dados = parse_json(dados_raw)
        faltando = []
        for campo, aliases in ALVOS.items():
            if valor_de_campo(dados, aliases) == "":
                faltando.append(campo)
        if faltando:
            pendencias.append((arquivo, faltando))
    return pendencias


def consolidado(rows):
    total = len(rows)
    stats = {k: 0 for k in ALVOS}
    for _, dados_raw in rows:
        dados = parse_json(dados_raw)
        for campo, aliases in ALVOS.items():
            if valor_de_campo(dados, aliases):
                stats[campo] += 1
    return total, stats


def reprocessar_pendencias(espera_segundos=8):
    rows_antes = carregar_ccts()
    total_antes, stats_antes = consolidado(rows_antes)
    pendencias = pendencias_por_arquivo(rows_antes)

    print("=== COBERTURA ANTES ===")
    print(f"Total CCTs: {total_antes}")
    for campo in ALVOS:
        print(f"{campo}: {stats_antes[campo]}/{total_antes}")

    if not pendencias:
        print("\nNenhuma pendência encontrada.")
        return

    print("\n=== LISTA DE PENDÊNCIAS ===")
    for i, (arquivo, faltando) in enumerate(pendencias, start=1):
        print(f"{i:02d}. {arquivo} -> faltando: {', '.join(faltando)}")

    print("\n=== CORREÇÃO SEQUENCIAL ===")
    quota_bloqueada = False

    def resolver_caminho_pdf(nome_arquivo):
        candidatos = [
            os.path.join(PASTA_PROCESSADOS, nome_arquivo),
            os.path.join(PASTA_NOVOS, nome_arquivo),
        ]
        for caminho in candidatos:
            if os.path.exists(caminho):
                return caminho
        return ""

    for i, (arquivo, faltando) in enumerate(pendencias, start=1):
        if quota_bloqueada:
            print(f"\n[{i}/{len(pendencias)}] Pulando {arquivo} por bloqueio de quota da API nesta execução.")
            continue

        caminho_pdf = resolver_caminho_pdf(arquivo)
        print(f"\n[{i}/{len(pendencias)}] Reprocessando {arquivo}")
        print(f"Pendências alvo: {', '.join(faltando)}")

        if not caminho_pdf:
            print(
                "[ERRO] Arquivo não encontrado nem em Processados nem em Novos: "
                f"{arquivo}"
            )
            continue

        try:
            dados_estruturados = extrair_dados_com_gemini(caminho_pdf)
            if not dados_estruturados:
                print("[ERRO] A extração não retornou dados.")
                continue

            dados_estruturados["arquivo_origem"] = arquivo
            salvar_cct_no_banco(dados_estruturados)
        except Exception as exc:
            print(f"[ERRO] Falha ao corrigir {arquivo}: {exc}")
            msg = str(exc).lower()
            if "erro na api (429)" in msg or "resource_exhausted" in msg or "quota" in msg:
                quota_bloqueada = True
                print("[AVISO] Quota da API atingida. Encerrando chamadas externas desta execução.")

        if i < len(pendencias) and not quota_bloqueada:
            print(f"Aguardando {espera_segundos}s para a próxima requisição...")
            time.sleep(espera_segundos)

    rows_depois = carregar_ccts()
    total_depois, stats_depois = consolidado(rows_depois)
    pendencias_restantes = pendencias_por_arquivo(rows_depois)

    print("\n=== COBERTURA DEPOIS ===")
    print(f"Total CCTs: {total_depois}")
    for campo in ALVOS:
        print(f"{campo}: {stats_depois[campo]}/{total_depois}")

    print("\n=== PENDÊNCIAS RESTANTES ===")
    if not pendencias_restantes:
        print("Nenhuma.")
    else:
        for i, (arquivo, faltando) in enumerate(pendencias_restantes, start=1):
            print(f"{i:02d}. {arquivo} -> faltando: {', '.join(faltando)}")


if __name__ == "__main__":
    reprocessar_pendencias(espera_segundos=8)
