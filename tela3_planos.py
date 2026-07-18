import streamlit as st

from config_banco import conectar_banco as abrir_banco
from core.leads_service import salvar_lead_comercial


def render_tela3_planos_precos(empresa_selecionada, cidade, uf):
    """Renderiza a Tela 3 com planos, CTA e captura de leads comerciais."""
    st.markdown("### 💼 Tela 3: Planos e Preços")
    st.caption("Estrutura comercial pronta para conversão com recomendação inteligente por perfil.")

    perfis = st.columns(3)
    with perfis[0]:
        st.metric("Escritório iniciante", "Até 5 empresas")
    with perfis[1]:
        st.metric("Operação em crescimento", "CNAE + Cargos")
    with perfis[2]:
        st.metric("Grupo empresarial", "Escala e automação")

    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(
            """
            <div class="pricing-card">
                <div class="pricing-sub">Plano de entrada</div>
                <h4>Básico</h4>
                <div class="pricing-price">R$ 199<span style='font-size:16px'>/mês</span></div>
                <div class="pricing-sub">Para validar risco sindical com baixo custo.</div>
                <ul>
                    <li>Até 5 empresas cadastradas</li>
                    <li>Consulta de CCT principal por CNAE</li>
                    <li>Painel técnico essencial</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Começar no Básico", key="plano_basico"):
            st.success("Lead do Básico registrado. Próximo passo: envio de proposta e onboarding guiado.")

    with p2:
        st.markdown(
            """
            <div class="pricing-card recommended">
                <span class="pricing-badge">RECOMENDADO</span>
                <div class="pricing-sub">Melhor custo-benefício</div>
                <h4>Profissional</h4>
                <div class="pricing-price">R$ 399<span style='font-size:16px'>/mês</span></div>
                <div class="pricing-sub">Ideal para escalar carteira com visão financeira.</div>
                <ul>
                    <li>Empresas ilimitadas</li>
                    <li>Cruzamento CNAE + Cargos</li>
                    <li>Impacto financeiro e cenários</li>
                    <li>Relatório operacional expandido</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Quero o Profissional", key="plano_profissional"):
            st.success("Lead do Profissional registrado com prioridade alta para fechamento.")

    with p3:
        st.markdown(
            """
            <div class="pricing-card">
                <div class="pricing-sub">Alta performance</div>
                <h4>Corporativo</h4>
                <div class="pricing-price">R$ 699+<span style='font-size:16px'>/mês</span></div>
                <div class="pricing-sub">Para grupos com exigência de automação avançada.</div>
                <ul>
                    <li>Alertas automáticos de vigência</li>
                    <li>Base multiunidade e governança</li>
                    <li>Ganchos para integrações futuras</li>
                    <li>Atendimento estratégico dedicado</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Falar com especialista", key="plano_corporativo"):
            st.success("Lead Corporativo registrado. Time comercial será acionado para diagnóstico consultivo.")

    st.write("---")
    st.markdown("#### 📞 CTA de Conversão")
    cta1, cta2, cta3 = st.columns(3)
    with cta1:
        nome_contato = st.text_input("Nome", key="contato_nome")
    with cta2:
        email_contato = st.text_input("E-mail", key="contato_email")
    with cta3:
        whatsapp_contato = st.text_input("WhatsApp", key="contato_whatsapp")

    plano_interesse = st.selectbox(
        "Plano de interesse",
        ["Básico", "Profissional", "Corporativo"],
        index=1,
        key="contato_plano",
    )

    if st.button("Receber proposta agora", key="cta_proposta"):
        if nome_contato and (email_contato or whatsapp_contato):
            cnae_contexto = ""
            if empresa_selecionada:
                cnae_contexto = empresa_selecionada.get("cnae", "")

            salvar_lead_comercial(
                nome=nome_contato,
                email=email_contato,
                whatsapp=whatsapp_contato,
                plano_interesse=plano_interesse,
                origem_tela="Tela 3 - Planos e Precos",
                cidade=cidade,
                uf=uf,
                cnae=cnae_contexto,
            )

            st.success(
                f"Contato registrado para o plano {plano_interesse}. "
                f"Prosseguir com proposta para {nome_contato}."
            )
        else:
            st.warning("Preencha ao menos nome e um canal de contato para finalizar o CTA.")

    with st.expander("📂 Últimos leads capturados", expanded=False):
        try:
            conn_leads = abrir_banco()
            cursor_leads = conn_leads.cursor()
            cursor_leads.execute(
                """
                SELECT nome, plano_interesse, email, whatsapp, cidade_contexto, uf_contexto, data_criacao
                FROM leads_comerciais
                ORDER BY id DESC
                LIMIT 10
                """
            )
            linhas_leads = cursor_leads.fetchall()
            conn_leads.close()

            if linhas_leads:
                tabela_leads = [
                    {
                        "Nome": l[0],
                        "Plano": l[1],
                        "Email": l[2] or "",
                        "WhatsApp": l[3] or "",
                        "Cidade": l[4] or "",
                        "UF": l[5] or "",
                        "Data": l[6],
                    }
                    for l in linhas_leads
                ]
                st.dataframe(tabela_leads, use_container_width=True)
            else:
                st.info("Ainda não existem leads capturados.")
        except Exception as e:
            st.error(f"Falha ao carregar leads: {e}")
