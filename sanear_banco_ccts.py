import sqlite3
from config_banco import obter_caminho_banco


def _is_numeric_text(value):
    return str(value or "").strip().isdigit()


def _nome_entidade(nome_fantasia, razao_social):
    nome = (nome_fantasia or "").strip()
    if nome:
        return nome
    nome = (razao_social or "").strip()
    if nome:
        return nome
    return "Nao Informado"


def sanear_ccts():
    db_path = obter_caminho_banco()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    ent_map = {}
    if cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='entidades'").fetchone()[0]:
        for ent_id, nome_fantasia, razao_social in cur.execute(
            "SELECT id, nome_fantasia, razao_social FROM entidades"
        ):
            ent_map[str(ent_id)] = _nome_entidade(nome_fantasia, razao_social)

    rows = cur.execute(
        """
        SELECT id, CAST(id_entidade_patronal AS TEXT), CAST(id_entidade_sindical AS TEXT)
        FROM ccts
        """
    ).fetchall()

    corrigidas = 0
    for cct_id, patronal, sindical in rows:
        novo_patronal = patronal
        novo_sindical = sindical

        if _is_numeric_text(patronal):
            novo_patronal = ent_map.get(str(patronal).strip(), "Nao Informado")

        if _is_numeric_text(sindical):
            novo_sindical = ent_map.get(str(sindical).strip(), "Nao Informado")

        if novo_patronal != patronal or novo_sindical != sindical:
            cur.execute(
                "UPDATE ccts SET id_entidade_patronal = ?, id_entidade_sindical = ? WHERE id = ?",
                (novo_patronal, novo_sindical, cct_id),
            )
            corrigidas += 1

    conn.commit()

    pend_patronal = cur.execute(
        "SELECT COUNT(*) FROM ccts WHERE TRIM(COALESCE(CAST(id_entidade_patronal AS TEXT), '')) GLOB '[0-9]*'"
    ).fetchone()[0]
    pend_sindical = cur.execute(
        "SELECT COUNT(*) FROM ccts WHERE TRIM(COALESCE(CAST(id_entidade_sindical AS TEXT), '')) GLOB '[0-9]*'"
    ).fetchone()[0]
    total_ccts = cur.execute("SELECT COUNT(*) FROM ccts").fetchone()[0]

    conn.close()

    print("Saneamento CCT concluido")
    print(f"Banco: {db_path}")
    print(f"Total CCTs: {total_ccts}")
    print(f"Linhas corrigidas: {corrigidas}")
    print(f"Pendencias patronal numerica: {pend_patronal}")
    print(f"Pendencias sindical numerica: {pend_sindical}")


if __name__ == "__main__":
    sanear_ccts()
