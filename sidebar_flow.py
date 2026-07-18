import streamlit as st
import core.painel_helpers as painel_helpers


resolver_entidades_cct = getattr(
    painel_helpers,
    "resolver_entidades_cct",
    lambda patronal, laboral, _arquivo: (patronal or "Não Informado", laboral or "Não Informado"),
)


ALIASES_CIDADE = {
    "MARINGA": ["MARINGA", "MGA", "SINCOMAR", "SINCONFEMAR", "SINTTROMAR", "SHESSMAR", "STESSMAR", "SINCONTABIL"],
    "FLORAI": ["FLORAI"],
    "SARANDI": ["SARANDI"],
    "PAICANDU": ["PAICANDU", "PAICANDU"],
    "CAMPO MOURAO": ["CAMPO MOURAO", "CAMPOMOURAO"],
    "JANDAIA DO SUL": ["JANDAIA", "JANDAIA DO SUL"],
}


def montar_filtro_consulta_livre(cursor, normalizar_texto):
    """Monta o fluxo lateral em 4 passos: UF -> Cidade -> Sindicato -> Instrumento."""
    st.sidebar.subheader("Fluxo de Enquadramento (Livre)")

    def documento_combina_com_cidade(cidade_normalizada, abrangencia_norm, arquivo_norm):
        if not cidade_normalizada:
            return False
        if cidade_normalizada in abrangencia_norm or cidade_normalizada in arquivo_norm:
            return True

        aliases = ALIASES_CIDADE.get(cidade_normalizada, [])
        if any(alias in arquivo_norm for alias in aliases):
            return True

        if cidade_normalizada == "MARINGA":
            aliases_outras_cidades = [
                alias
                for cidade, lista in ALIASES_CIDADE.items()
                if cidade != "MARINGA"
                for alias in lista
            ]
            if any(alias in arquivo_norm for alias in aliases_outras_cidades):
                return False
            if "PARANA" in abrangencia_norm:
                return True

        return False

    def carregar_sindicatos_ccts(uf_normalizada, cidade_normalizada):
        sindicatos = []
        cursor.execute(
            """
            SELECT id, id_entidade_patronal, id_entidade_sindical,
                   COALESCE(abrangencia_territorial, ''), COALESCE(arquivo_origem, ''),
                   vigencia_inicio, vigencia_fim
            FROM ccts
            ORDER BY id DESC
            """
        )

        for r in cursor.fetchall():
            registro_id, patronal_raw, laboral_raw, abrangencia, arquivo_origem, vigencia_inicio, vigencia_fim = r
            abrangencia_norm = normalizar_texto(abrangencia)
            arquivo_norm = normalizar_texto(arquivo_origem)

            escopo = None
            if documento_combina_com_cidade(cidade_normalizada, abrangencia_norm, arquivo_norm):
                escopo = "cidade"
            elif uf_normalizada and uf_normalizada in abrangencia_norm:
                escopo = "uf"

            if not escopo:
                continue

            patronal, laboral = resolver_entidades_cct(patronal_raw, laboral_raw, arquivo_origem)
            sindicatos.append(
                {
                    "fonte": "ccts",
                    "escopo": escopo,
                    "id": registro_id,
                    "patronal": patronal,
                    "laboral": laboral,
                    "arquivo_origem": arquivo_origem,
                    "vigencia_inicio": vigencia_inicio,
                    "vigencia_fim": vigencia_fim,
                }
            )

        sindicatos_cidade = [s for s in sindicatos if s["escopo"] == "cidade"]
        return sindicatos_cidade if sindicatos_cidade else [s for s in sindicatos if s["escopo"] == "uf"]

    def carregar_sindicatos_relacionais(uf_normalizada, cidade_normalizada):
        cursor.execute(
            """
            SELECT DISTINCT
                   COALESCE(s.sindicato_patronal, 'Patronal não identificado') AS patronal,
                   COALESCE(s.sindicato_laboral, 'Laboral não identificado') AS laboral
            FROM sindicatos s
            JOIN matriz_enquadramento m ON m.sindicato_id = s.id
            WHERE UPPER(TRIM(m.uf)) = ?
              AND UPPER(TRIM(m.municipio)) = ?
            ORDER BY patronal, laboral
            """,
            (uf_normalizada, cidade_normalizada),
        )
        return [
            {"fonte": "sindicatos", "patronal": r[0], "laboral": r[1]}
            for r in cursor.fetchall()
            if r is not None and len(r) >= 2
        ]

    cursor.execute(
        """
        SELECT DISTINCT UPPER(TRIM(uf))
        FROM matriz_enquadramento
        WHERE uf IS NOT NULL AND TRIM(uf) <> ''
        ORDER BY 1
        """
    )
    lista_ufs = [u[0] for u in cursor.fetchall() if u[0]]
    if not lista_ufs:
        lista_ufs = ["PR", "RJ"]

    placeholder_uf = "Selecione um estado"
    opcoes_uf = [placeholder_uf] + lista_ufs
    uf_escolhida = st.sidebar.selectbox("1. Estado (UF)", opcoes_uf, key="manual_uf")
    uf_valida = uf_escolhida != placeholder_uf

    lista_cidades = []
    if uf_valida:
        cursor.execute(
            """
            SELECT DISTINCT UPPER(TRIM(municipio))
            FROM matriz_enquadramento
            WHERE UPPER(TRIM(uf)) = ?
              AND municipio IS NOT NULL AND TRIM(municipio) <> ''
            ORDER BY 1
            """,
            (normalizar_texto(uf_escolhida),),
        )
        lista_cidades = [c[0] for c in cursor.fetchall() if c[0]]

    placeholder_cidade = "Selecione uma cidade"
    opcoes_cidade = [placeholder_cidade] + lista_cidades if lista_cidades else [placeholder_cidade]
    cidade_escolhida = st.sidebar.selectbox("2. Cidade", opcoes_cidade, key="manual_cidade", disabled=not uf_valida)
    cidade_valida = uf_valida and cidade_escolhida != placeholder_cidade

    sindicato_opcoes = []
    documentos_cct = []
    if cidade_valida:
        uf_normalizada = normalizar_texto(uf_escolhida)
        cidade_normalizada = normalizar_texto(cidade_escolhida)
        documentos_cct = carregar_sindicatos_ccts(uf_normalizada, cidade_normalizada)
        if documentos_cct:
            sindicato_opcoes.extend(documentos_cct)
        else:
            sindicato_opcoes.extend(carregar_sindicatos_relacionais(uf_normalizada, cidade_normalizada))

    vistos = set()
    sindicato_filtrado = []
    for s in sindicato_opcoes:
        if not isinstance(s, dict):
            continue
        patronal = s.get("patronal")
        laboral = s.get("laboral")
        if patronal is None or laboral is None:
            continue
        chave = (patronal, laboral)
        if chave not in vistos:
            vistos.add(chave)
            sindicato_filtrado.append(s)

    sindicato_escolhido = None
    instrumento_escolhido = None

    if sindicato_filtrado and cidade_valida:
        mapa_sindicatos = {}
        for s in sindicato_filtrado:
            label = f"{s['patronal']} vs {s['laboral']}"
            if label in mapa_sindicatos:
                label = f"{label} [{s['fonte']}]"
            mapa_sindicatos[label] = s

        placeholder_sindicato = "Selecione um sindicato"
        opcoes_sindicato = [placeholder_sindicato] + list(mapa_sindicatos.keys())
        sindicato_label = st.sidebar.selectbox("3. Sindicato", opcoes_sindicato, key="manual_sindicato")
        if sindicato_label == placeholder_sindicato:
            sindicato_escolhido = None
        else:
            sindicato_escolhido = mapa_sindicatos[sindicato_label]

        if sindicato_escolhido and sindicato_escolhido.get("fonte") == "ccts" and sindicato_escolhido.get("escopo") == "uf":
            st.sidebar.caption("Exibindo fallback estadual porque não houve instrumento vinculado diretamente à cidade selecionada.")
        elif sindicato_escolhido and sindicato_escolhido.get("fonte") == "sindicatos":
            st.sidebar.caption("Exibindo fallback relacional porque não houve CCT aderente para a cidade selecionada.")

        instrumentos = []
        if sindicato_escolhido and sindicato_escolhido["fonte"] == "sindicatos":
            cursor.execute(
                """
                SELECT s.id, s.vigencia
                FROM sindicatos s
                JOIN matriz_enquadramento m ON m.sindicato_id = s.id
                WHERE UPPER(TRIM(m.uf)) = ?
                  AND UPPER(TRIM(m.municipio)) = ?
                  AND COALESCE(s.sindicato_patronal, 'Patronal não identificado') = ?
                  AND COALESCE(s.sindicato_laboral, 'Laboral não identificado') = ?
                ORDER BY s.id DESC
                """,
                (
                    normalizar_texto(uf_escolhida),
                    normalizar_texto(cidade_escolhida),
                    sindicato_escolhido["patronal"],
                    sindicato_escolhido["laboral"],
                ),
            )
            instrumentos = [
                {"fonte": "sindicatos", "id": r[0], "label": f"Instrumento #{r[0]} | Vigência: {r[1] or 'N/D'}"}
                for r in cursor.fetchall()
                if r is not None and len(r) >= 2
            ]
        elif sindicato_escolhido:
            documentos_filtrados = [
                d for d in documentos_cct
                if isinstance(d, dict)
                and d.get("patronal") == sindicato_escolhido.get("patronal")
                and d.get("laboral") == sindicato_escolhido.get("laboral")
            ]
            instrumentos = [
                {
                    "fonte": "ccts",
                    "id": d["id"],
                    "label": f"{d['arquivo_origem']} | {d['vigencia_inicio'] or 'N/D'} até {d['vigencia_fim'] or 'N/D'}",
                }
                for d in documentos_filtrados
            ]

        if instrumentos:
            mapa_instr = {i["label"]: i for i in instrumentos}
            placeholder_instr = "Selecione um instrumento coletivo"
            opcoes_instr = [placeholder_instr] + list(mapa_instr.keys())
            instr_label = st.sidebar.selectbox("4. Instrumento Coletivo", opcoes_instr, key="manual_instrumento", disabled=sindicato_escolhido is None)
            if instr_label != placeholder_instr:
                instrumento_escolhido = mapa_instr[instr_label]
        elif sindicato_escolhido:
            st.sidebar.warning("Nenhum instrumento coletivo encontrado para o sindicato selecionado.")
    elif cidade_valida:
        st.sidebar.warning("Nenhum sindicato encontrado para UF/Cidade selecionadas.")

    return {
        "uf": uf_escolhida if uf_valida else None,
        "cidade": cidade_escolhida if cidade_valida else None,
        "modo": "manual",
        "sindicato": sindicato_escolhido,
        "instrumento": instrumento_escolhido,
    }
