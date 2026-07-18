import streamlit as st


def render_alerta_colorido(nivel, mensagem):
    """Renderiza alerta com estilo visual diferente por severidade."""
    estilos = {
        "CRITICO": ("#7F1D1D", "#FEE2E2", "🚨 CRÍTICO"),
        "ATENCAO": ("#92400E", "#FEF3C7", "🟡 ATENÇÃO"),
        "INFO": ("#1E3A8A", "#DBEAFE", "🔵 INFO"),
    }
    cor_texto, cor_fundo, titulo = estilos.get(nivel, estilos["INFO"])
    st.markdown(
        f"""
        <div style="border-left: 6px solid {cor_texto}; background: {cor_fundo};
                    padding: 10px 12px; border-radius: 8px; margin-bottom: 8px;">
            <strong style="color:{cor_texto};">{titulo}</strong><br>
            <span style="color:#1F2937;">{mensagem}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_card_cct(cct):
    texto_laboral_completo = cct.get("laboral", "")
    if texto_laboral_completo:
        siglas = [
            bloco.strip().split()[0]
            for bloco in texto_laboral_completo.split(",")
            if bloco.strip() and bloco.strip().split()
        ]
        laboral_exibicao = " / ".join(siglas) if siglas else texto_laboral_completo
    else:
        laboral_exibicao = "Não Informado"

    st.warning(f"ℹ️ **Sindicato Patronal:** {cct['patronal']}\n\n🤝 **Sindicato Laboral:** {laboral_exibicao}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📅 Vigência", cct["vigencia"])
    with c2:
        st.metric("💵 Piso Garantido", cct["piso"])
    with c3:
        st.metric("📈 Reajuste", cct["reajuste"])

    cb1, cb2 = st.columns(2)
    with cb1:
        st.info(f"🍔 **Vale Refeição:**\n\n{cct['va']}")
    with cb2:
        st.info(f"🍼 **Auxílio Creche:**\n\n{cct['creche']}")

    st.error(f"⚠️ **Alerta Legal de Cláusula Crítica:**\n\n{cct['critica']}")

    if cct.get("dados_completo"):
        with st.expander("🔍 Visualizar Resumo e Análise Multimodal da IA", expanded=False):
            st.markdown(cct["dados_completo"])
