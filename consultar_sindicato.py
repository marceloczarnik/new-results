import sqlite3
import sys

from config_banco import conectar_banco

# Garante que o terminal do Windows exiba acentos corretamente
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def descobrir_estrutura():
    """Descobre o nome real da tabela e das colunas para evitar erros de digitação anteriores"""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [row[0] for row in cursor.fetchall()]

    if not tabelas:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sindicatos (
                id TEXT PRIMARY KEY,
                sindicato_patronal TEXT NOT NULL,
                sindicato_laboral TEXT NOT NULL,
                vigencia TEXT,
                piso_salarial TEXT,
                reajuste_salarial TEXT,
                vale_refeicao TEXT,
                auxilio_creche TEXT,
                clausula_critica TEXT
            )
        """)
        conn.commit()
        tabelas = ["sindicatos"]

    nome_tabela = "sindicatos"
    if "sindicatos" in tabelas:
        nome_tabela = "sindicatos"
    elif "sindicato" in tabelas:
        nome_tabela = "sindicato"
    elif "santicatos" in tabelas:
        nome_tabela = "santicatos"

    try:
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        colunas = [col[1] for col in cursor.fetchall()]
    except sqlite3.OperationalError:
        colunas = []

    conn.close()
    return nome_tabela, colunas

def buscar_convencao():
    nome_tabela, colunas = descobrir_estrutura()

    if "sindicato_patronal" not in colunas or "sindicato_laboral" not in colunas:
        print("\n⚠️ Estrutura de banco incompatível com a consulta.\n")
        print("A tabela 'sindicatos' precisa existir com as colunas 'sindicato_patronal' e 'sindicato_laboral'.")
        return

    print("\n" + "=" * 60)
    print("         SISTEMA SINDICAL - MOTOR DE BUSCA RÁPIDA         ")
    print("=" * 60)
    termo = input("🔍 Digite o nome do Sindicato (Patronal ou Laboral): ").strip()
    
    if not termo:
        print("❌ Digite um termo válido.")
        return

    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Busca flexível por aproximação (LIKE)
    query = f"""
        SELECT * FROM {nome_tabela} 
        WHERE sindicato_patronal LIKE ? OR sindicato_laboral LIKE ?
    """
    cursor.execute(query, (f"%{termo}%", f"%{termo}%"))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(f"\nℹ️ Nenhuma convenção encontrada para o termo: '{termo}'")
        return

    print(f"\n✨ Encontrado(s) {len(resultados)} registro(s):")
    
    for reg in resultados:
        dados = dict(zip(colunas, reg))
        
        print("-" * 60)
        print(f"🆔 ID: {dados.get('id')}")
        print(f"🏢 Patronal: {dados.get('sindicato_patronal')}")
        print(f"🤝 Laboral: {dados.get('sindicato_laboral')}")
        print(f"📅 Vigência: {dados.get('vigencia')}")
        print(f"💰 Piso Salarial: {dados.get('piso_salarial')}")
        print(f"📈 Reajuste: {dados.get('reajuste_salarial')}")
        
        # Flexibilidade para diferentes nomes de colunas de benefícios
        va = dados.get('vale_alimentacao') or dados.get('vale_alimentacao_descricao') or "Não informado"
        creche = dados.get('auxilio_creche') or dados.get('auxilio_creche_descricao') or "Não informado"
        
        print(f"🍞 Vale Alimentação: {va}")
        print(f"🍼 Auxílio Creche: {creche}")
        print(f"⚠️ CLÁUSULA CRÍTICA: {dados.get('clausula_critica')}")
    print("-" * 60)

if __name__ == "__main__":
    while True:
        buscar_convencao()
        if input("\n🔄 Nova consulta? (S/N): ").strip().upper() != 'S':
            print("\nEncerrando motor de busca. Até logo!")
            break