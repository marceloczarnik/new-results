import re
import unicodedata


GENERICOS_CCT = {
    "PATRONAL",
    "LABORAL",
    "NAO IDENTIFICADO",
    "NÃO IDENTIFICADO",
    "PATRONAL NAO INFORMADO",
    "LABORAL NAO INFORMADO",
    "PATRONAL NÃO INFORMADO",
    "LABORAL NÃO INFORMADO",
}

TOKENS_IGNORADOS_CCT = {
    "CONVENCAO",
    "CONVENÇÃO",
    "ADITIVO",
    "TERMO",
    "TAXA",
    "CONTRIBUICAO",
    "CONTRIBUIÇÃO",
    "CONJUNTO",
    "CCT",
    "ACORDO",
    "COLETIVA",
    "TRABALHO",
    "PARANA",
    "PARANÁ",
    "BRASIL",
    "PR",
    "MARINGA",
    "MARINGÁ",
    "SARANDI",
    "PAICANDU",
    "PAIÇANDU",
    "FLORAI",
}

CIDADES_CCT = {
    "MARINGA": ("Maringá, Paraná", ["MARINGA", "MGA", "SINCOMAR", "SINCONFEMAR", "SINTTROMAR", "SHESSMAR", "STESSMAR", "SINCONTABIL", "SINDEPRESTEM", "SOE"]),
    "FLORAI": ("Floraí, Paraná", ["FLORAI"]),
    "SARANDI": ("Sarandi, Paraná", ["SARANDI"]),
    "PAICANDU": ("Paiçandu, Paraná", ["PAICANDU", "PAICANDU"]),
    "CAMPO MOURAO": ("Campo Mourão, Paraná", ["CAMPO MOURAO", "CAMPOMOURAO"]),
    "JANDAIA DO SUL": ("Jandaia do Sul, Paraná", ["JANDAIA", "JANDAIA DO SUL"]),
}

TIPOS_INSTRUMENTO_VALIDOS = ("CONVENCAO", "CONVENÇÃO", "ADITIVO", "TERMO", "ACORDO")


def normalizar_texto(texto):
    if not texto:
        return ""
    texto_limpo = "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )
    return texto_limpo.upper().strip()


def extrair_valor_monetario(texto):
    """Extrai o primeiro valor monetário de uma string e converte para float."""
    if texto is None:
        return 0.0

    bruto = str(texto)
    padrao = r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)"
    encontrado = re.search(padrao, bruto)
    if not encontrado:
        return 0.0

    numero = encontrado.group(1).replace(".", "").replace(",", ".")
    try:
        return float(numero)
    except ValueError:
        return 0.0


def extrair_percentual(texto):
    """Extrai o primeiro percentual numérico encontrado na string."""
    if texto is None:
        return 0.0

    bruto = str(texto)
    encontrado = re.search(r"(\d+(?:[\.,]\d+)?)", bruto)
    if not encontrado:
        return 0.0

    numero = encontrado.group(1).replace(",", ".")
    try:
        return float(numero)
    except ValueError:
        return 0.0


def classificar_alerta(critica):
    """Classifica severidade de alerta com base em palavras-chave de risco."""
    if not critica:
        return "INFO"

    texto = str(critica).lower()
    if any(p in texto for p in ["multa", "penal", "autua", "process", "interdição", "critica"]):
        return "CRITICO"
    if any(p in texto for p in ["jornada", "interval", "adicional", "insalubr", "periculos", "banco de horas"]):
        return "ATENCAO"
    return "INFO"


def valor_generico_cct(valor):
    texto = normalizar_texto(valor)
    return not texto or texto in GENERICOS_CCT


def derivar_siglas_cct_do_arquivo(nome_arquivo):
    if not nome_arquivo:
        return "Não Informado", "Não Informado"

    bruto = str(nome_arquivo).replace(".pdf", "").replace(".PDF", "")
    partes = [p for p in re.split(r"[\s_\-]+", bruto) if p]

    uteis = []
    for parte in partes:
        texto_norm = normalizar_texto(parte)
        if not texto_norm or texto_norm.isdigit():
            continue
        if texto_norm in TOKENS_IGNORADOS_CCT:
            continue
        uteis.append(parte.upper())

    if len(uteis) >= 2:
        return uteis[0], uteis[1]
    if len(uteis) == 1:
        return uteis[0], "Instrumento Coletivo"
    return "Não Informado", "Não Informado"


def resolver_entidades_cct(patronal, laboral, arquivo_origem):
    patronal_resolvido = patronal or ""
    laboral_resolvido = laboral or ""

    if valor_generico_cct(patronal_resolvido) or valor_generico_cct(laboral_resolvido):
        patronal_arquivo, laboral_arquivo = derivar_siglas_cct_do_arquivo(arquivo_origem)
        if valor_generico_cct(patronal_resolvido):
            patronal_resolvido = patronal_arquivo
        if valor_generico_cct(laboral_resolvido):
            laboral_resolvido = laboral_arquivo

    return patronal_resolvido or "Não Informado", laboral_resolvido or "Não Informado"


def arquivo_parece_instrumento_coletivo(nome_arquivo):
    nome_norm = normalizar_texto(nome_arquivo)
    return any(token in nome_norm for token in TIPOS_INSTRUMENTO_VALIDOS)


def inferir_abrangencia_cct(arquivo_origem, abrangencia_atual=""):
    abrangencia_norm = normalizar_texto(abrangencia_atual)
    if abrangencia_norm and abrangencia_norm not in {"PARANA", "PARANA, BRASIL", "PARANÁ", "PARANÁ, BRASIL", "BRASIL", "NAO INFORMADA", "NÃO INFORMADA"}:
        return abrangencia_atual

    arquivo_norm = normalizar_texto(arquivo_origem)
    cidades_encontradas = []
    for _, (rotulo, aliases) in CIDADES_CCT.items():
        if any(alias in arquivo_norm for alias in aliases):
            cidades_encontradas.append(rotulo)

    if cidades_encontradas:
        vistos = []
        for cidade in cidades_encontradas:
            if cidade not in vistos:
                vistos.append(cidade)
        return ", ".join(vistos)

    if "PARANA" in arquivo_norm or "PARANÁ" in arquivo_norm or "PR" in arquivo_norm:
        return "Paraná"
    return abrangencia_atual or "Não Informada"


def inferir_titulo_cct(arquivo_origem, vigencia_inicio="", vigencia_fim=""):
    nome_norm = normalizar_texto(arquivo_origem)
    if "ADITIVO" in nome_norm:
        return f"Aditivo Coletivo {vigencia_inicio}-{vigencia_fim}".strip("-")
    if "TERMO" in nome_norm:
        return f"Termo Coletivo {vigencia_inicio}-{vigencia_fim}".strip("-")
    if "ACORDO" in nome_norm:
        return f"Acordo Coletivo {vigencia_inicio}-{vigencia_fim}".strip("-")
    return f"Convenção Coletiva {vigencia_inicio}-{vigencia_fim}".strip("-")
