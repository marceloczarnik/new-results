import sqlite3
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def conectar_banco():
    return sqlite3.connect("banco_sindical.db")

def descobrir_estrutura():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [row[0] for row in cursor.fetchall()]
    nome_tabela = "sindicato" if "sindicato" in tabelas else ("santicatos" if "santicatos" in tabelas else "sindicatos")
    cursor.execute(f"PRAGMA table_info({nome_tabela})")
    colunas = [col[1] for col in cursor.fetchall()]
    conn.close()
    return nome_tabela, colunas

def gerar_painel():
    nome_tabela, colunas = descobrir_estrutura()
    
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {nome_tabela}")
    registros = cursor.fetchall()
    conn.close()

    print("\n" + "=" * 60)
    print("       🚨 PAINEL DE CONVENÇÕES E ALERTAS CRÍTICOS 🚨       ")
    print("=" * 60)

    if not registros:
        print("ℹ️ Banco de dados vazio ou nenhuma convenção cadastrada.")
        return

    alertas_encontrados = 0

    for reg in registros:
        dados = dict(zip(colunas, reg))
        clausula = dados.get('clausula_critica', '')
        vigencia = dados.get('vigencia', '')

        e_critico = False
        motivo = []

        # Regra 1: Alerta de vigência atual (2026)
        if "2026" in str(vigencia):
            e_critico = True
            motivo.append("Vigência atual (2026) - Necessita acompanhar dissídio/revisão")
        
        # Regra 2: Termos de alto impacto na cláusula crítica extraída pela IA
        if clausula and any(termo in clausula.lower() for termo in ["multa", "obrigatório", "contribuição", "atenção", "rh", "seguro"]):
            e_critico = True
            motivo.append("Cláusula de alto impacto financeiro/legal detectada")

        if e_critico:
            alertas_encontrados += 1
            print(f"\n🚨 ALERTA #{alertas_encontrados}")
            print(f"🏢 Patronal: {dados.get('sindicato_patronal')}")
            print(f"🤝 Laboral: {dados.get('sindicato_laboral')}")
            print(f"📅 Vigência: {vigencia}")
            print(f"📌 Motivos: {', '.join(motivo)}")
            print(f"⚠️ Resumo da Cláusula: {clausula}")
            print("-" * 60)

    if alertas_encontrados == 0:
        print("✅ Tudo sob controle! Nenhuma inconformidade ou vencimento crítico listado.")
    else:
        print(f"\nFim do relatório. Total de {alertas_encontrados} sindicato(s) exigindo atenção.")

if __name__ == "__main__":
    gerar_painel()
    input("\nPressione Enter para fechar o painel...")