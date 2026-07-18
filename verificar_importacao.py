import sqlite3
import os

db_path = os.path.join("dados", "dados_sindicais.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM ccts")
total = cursor.fetchone()[0]

cursor.execute("SELECT arquivo_origem FROM ccts ORDER BY id")
arquivos = cursor.fetchall()

with open("resultado_importacao.txt", "w", encoding="utf-8") as f:
    f.write(f"TOTAL DE CCTS: {total}\n\n")
    f.write("ARQUIVOS IMPORTADOS:\n")
    for i, row in enumerate(arquivos, 1):
        f.write(f"{i:2}. {row[0]}\n")

conn.close()
print(f"Resultado salvo em resultado_importacao.txt")
print(f"Total: {total}")
