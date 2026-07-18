import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANONICAL_DB = os.path.join(BASE_DIR, "dados", "dados_sindicais.db")
LEGACY_DB = os.path.join(BASE_DIR, "banco_sindical.db")


def obter_caminho_banco() -> str:
    """Retorna o banco canônico do sistema, com fallback seguro para o legado."""
    if os.path.exists(CANONICAL_DB):
        return CANONICAL_DB
    if os.path.exists(LEGACY_DB):
        return LEGACY_DB
    return CANONICAL_DB


def conectar_banco() -> sqlite3.Connection:
    """Abre uma conexão para o banco canônico do projeto."""
    return sqlite3.connect(obter_caminho_banco())
