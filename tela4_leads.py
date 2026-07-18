import csv
import io
import zipfile
from datetime import date, datetime

import streamlit as st

from core.leads_service import (
    carregar_leads,
    atualizar_status_lead,
    carregar_historico_movimentacoes,
    carregar_alertas_sla,
    carregar_metricas_performance,
    carregar_metricas_por_plano,
)


def render_tela4_gestao_leads():
    """Renderiza a Tela 4 completa de operação comercial de leads."""
    st.markdown("### 📂 Tela 4: Gestão de Leads")
    st.caption("Operação comercial com filtros, priorização e exportação de oportunidades.")

    if "visao_rapida_status" not in st.session_state:
        st.session_state["visao_rapida_status"] = ["NOVO", "EM_CONTATO", "PROPOSTA_ENVIADA", "GANHO", "PERDIDO"]

    st.markdown("#### ⚡ Visões rápidas")
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        if st.button("Todos", key="visao_todos"):
            st.session_state["visao_rapida_status"] = ["NOVO", "EM_CONTATO", "PROPOSTA_ENVIADA", "GANHO", "PERDIDO"]
    with v2:
        if st.button("Somente NOVO", key="visao_novo"):
            st.session_state["visao_rapida_status"] = ["NOVO"]
    with v3:
        if st.button("Proposta enviada", key="visao_proposta"):
            st.session_state["visao_rapida_status"] = ["PROPOSTA_ENVIADA"]
    with v4:
        if st.button("Ganhos", key="visao_ganho"):
            st.session_state["visao_rapida_status"] = ["GANHO"]

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        filtro_planos = st.multiselect(
            "Filtrar por plano",
            ["Básico", "Profissional", "Corporativo"],
            default=["Básico", "Profissional", "Corporativo"],
        )
    with colf2:
        filtro_status = st.multiselect(
            "Filtrar por status",
            ["NOVO", "EM_CONTATO", "PROPOSTA_ENVIADA", "GANHO", "PERDIDO"],
            default=st.session_state.get("visao_rapida_status", ["NOVO", "EM_CONTATO", "PROPOSTA_ENVIADA", "GANHO", "PERDIDO"]),
            key="filtro_status_leads",
        )
    with colf3:
        busca_nome = st.text_input("Buscar por nome")

    periodo = st.date_input("Período de captura", value=(date.today(), date.today()))
    data_ini = None
    data_fim = None
    if isinstance(periodo, tuple) and len(periodo) == 2:
        data_ini, data_fim = periodo

    leads = carregar_leads(
        planos=filtro_planos,
        status=filtro_status,
        busca_nome=busca_nome,
        data_inicial=data_ini,
        data_final=data_fim,
    )

    total_leads = len(leads)
    ganhos = len([l for l in leads if l[3] == "GANHO"])
    novos = len([l for l in leads if l[3] == "NOVO"])
    taxa_ganho = round((ganhos / total_leads) * 100, 2) if total_leads else 0.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Leads no filtro", total_leads)
    with m2:
        st.metric("Novos", novos)
    with m3:
        st.metric("Taxa de ganho", f"{taxa_ganho}%")

    st.markdown("#### ⏱️ SLA Operacional")
    horas_sla = st.number_input("Limite de SLA (horas) para status NOVO", min_value=1, value=48, step=1)
    alertas_sla = carregar_alertas_sla(horas_limite=horas_sla, data_inicial=data_ini, data_final=data_fim)
    criticos_72h = 0
    atencao_48h = 0

    if alertas_sla:
        st.error(f"{len(alertas_sla)} lead(s) em risco de SLA acima de {horas_sla}h.")

        criticos_72h = len([a for a in alertas_sla if float(a[5]) >= 72])
        atencao_48h = len([a for a in alertas_sla if 48 <= float(a[5]) < 72])
        monitorar = len([a for a in alertas_sla if float(a[5]) < 48])

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("🔴 Crítico (>=72h)", criticos_72h)
        with s2:
            st.metric("🟡 Atenção (48-71h)", atencao_48h)
        with s3:
            st.metric("🔵 Monitorar (<48h)", monitorar)

        if criticos_72h > 0:
            st.error("Existem leads críticos com mais de 72h sem evolução.")
        elif atencao_48h > 0:
            st.warning("Existem leads em atenção entre 48h e 71h.")
        else:
            st.info("Leads acima do SLA configurado, mas ainda fora das faixas críticas padrão.")

        tabela_sla = [
            {
                "Lead ID": a[0],
                "Nome": a[1],
                "Plano": a[2],
                "Email": a[3] or "",
                "WhatsApp": a[4] or "",
                "Horas em NOVO": a[5],
                "Prioridade": "CRÍTICO" if float(a[5]) >= 72 else ("ATENÇÃO" if float(a[5]) >= 48 else "MONITORAR"),
                "Criado em": a[6],
            }
            for a in alertas_sla
        ]
        st.dataframe(tabela_sla, use_container_width=True)
    else:
        st.success("Nenhum lead em NOVO ultrapassou o SLA no período filtrado.")

    st.markdown("#### 📈 Performance Comercial (Período)")
    perf = carregar_metricas_performance(data_inicial=data_ini, data_final=data_fim)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Entradas no período", perf["entradas"])
    with p2:
        st.metric("Conversões (GANHO)", perf["ganhos"])
    with p3:
        st.metric("Taxa de conversão", f"{perf['taxa_conversao']}%")

    meta_conversao = st.number_input(
        "Meta mensal de conversão (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
    )
    atingimento = round((perf["taxa_conversao"] / meta_conversao) * 100, 2) if meta_conversao > 0 else 0.0
    gap_meta = round(perf["taxa_conversao"] - meta_conversao, 2)

    m_meta1, m_meta2 = st.columns(2)
    with m_meta1:
        st.metric("Atingimento da meta", f"{atingimento}%")
    with m_meta2:
        st.metric("Gap vs meta", f"{gap_meta}%")

    progresso = min(max(perf["taxa_conversao"] / meta_conversao, 0.0), 1.0) if meta_conversao > 0 else 0.0
    st.progress(progresso)

    if perf["taxa_conversao"] >= meta_conversao:
        st.success("Meta mensal de conversão atingida no período filtrado.")
    else:
        st.warning("Meta mensal de conversão ainda não atingida no período filtrado.")

    st.markdown("#### 🎯 Metas por Plano")
    mp1, mp2, mp3 = st.columns(3)
    with mp1:
        meta_basico = st.number_input("Meta Básico (%)", min_value=0.0, max_value=100.0, value=18.0, step=1.0)
    with mp2:
        meta_prof = st.number_input("Meta Profissional (%)", min_value=0.0, max_value=100.0, value=28.0, step=1.0)
    with mp3:
        meta_corp = st.number_input("Meta Corporativo (%)", min_value=0.0, max_value=100.0, value=35.0, step=1.0)

    metas_por_plano = {
        "Básico": meta_basico,
        "Profissional": meta_prof,
        "Corporativo": meta_corp,
    }
    metricas_planos = carregar_metricas_por_plano(data_inicial=data_ini, data_final=data_fim)

    tabela_planos = []
    for plano, entradas_plano, ganhos_plano in metricas_planos:
        entradas_plano = entradas_plano or 0
        ganhos_plano = ganhos_plano or 0
        taxa_real = round((ganhos_plano / entradas_plano) * 100, 2) if entradas_plano else 0.0
        meta_plano = metas_por_plano.get(plano, 0.0)
        gap_plano = round(taxa_real - meta_plano, 2)
        status_meta = "ATINGIDA" if taxa_real >= meta_plano else "ABAIXO"

        tabela_planos.append(
            {
                "Plano": plano,
                "Entradas": entradas_plano,
                "Ganhos": ganhos_plano,
                "Taxa real (%)": taxa_real,
                "Meta (%)": meta_plano,
                "Gap (%)": gap_plano,
                "Status meta": status_meta,
            }
        )

    if tabela_planos:
        st.dataframe(tabela_planos, use_container_width=True)
        st.bar_chart(
            {
                row["Plano"]: [row["Taxa real (%)"]]
                for row in tabela_planos
            }
        )
    else:
        st.info("Sem dados de leads no período para medir metas por plano.")

    st.markdown("#### 🧭 Resumo Executivo Automático")
    gargalo_etapa = None
    maior_tempo = 0.0
    for etapa, horas in perf.get("tempo_medio_etapas", []):
        horas_num = float(horas or 0)
        if horas_num > maior_tempo:
            maior_tempo = horas_num
            gargalo_etapa = etapa

    distribuicao = perf.get("distribuicao_etapas", [])
    etapa_mais_frequente = distribuicao[0][0] if distribuicao else "N/D"

    resumo_linhas = [
        f"Entradas no período: {perf['entradas']} | Conversões: {perf['ganhos']} | Taxa: {perf['taxa_conversao']}%",
        f"SLA crítico (>=72h): {criticos_72h} lead(s) | Atenção (48-71h): {atencao_48h} lead(s)",
        f"Etapa mais recorrente nas movimentações: {etapa_mais_frequente}",
    ]
    if gargalo_etapa:
        resumo_linhas.append(f"Maior tempo médio por etapa: {gargalo_etapa} ({maior_tempo}h)")

    for linha in resumo_linhas:
        st.markdown(f"- {linha}")

    acoes = []
    if criticos_72h > 0:
        acoes.append("Priorizar força-tarefa para leads críticos acima de 72h ainda em NOVO.")
    if perf["taxa_conversao"] < meta_conversao:
        acoes.append("Reforçar follow-up de PROPOSTA_ENVIADA com cadência comercial em até 24h.")
    if gargalo_etapa in ["EM_CONTATO", "PROPOSTA_ENVIADA"]:
        acoes.append("Criar playbook para destravar a etapa com maior tempo médio.")
    if not acoes:
        acoes.append("Manter rotina atual e replicar abordagem dos casos GANHO para os demais leads.")

    st.markdown("**Ações recomendadas:**")
    for acao in acoes:
        st.markdown(f"- {acao}")

    st.markdown("#### 📤 Exportar Resumo Executivo")
    periodo_texto = f"{data_ini} a {data_fim}" if data_ini and data_fim else "Período não definido"

    linhas_markdown = [
        "# Resumo Executivo Comercial",
        "",
        f"Período analisado: {periodo_texto}",
        "",
        "## Indicadores Gerais",
        f"- Entradas: {perf['entradas']}",
        f"- Conversões (GANHO): {perf['ganhos']}",
        f"- Taxa de conversão: {perf['taxa_conversao']}%",
        f"- Meta mensal: {meta_conversao}%",
        f"- Atingimento da meta: {atingimento}%",
        f"- Gap vs meta: {gap_meta}%",
        "",
        "## SLA",
        f"- Leads críticos (>=72h): {criticos_72h}",
        f"- Leads atenção (48-71h): {atencao_48h}",
        "",
        "## Gargalos",
        f"- Etapa mais recorrente: {etapa_mais_frequente}",
    ]

    if gargalo_etapa:
        linhas_markdown.append(f"- Maior tempo médio: {gargalo_etapa} ({maior_tempo}h)")

    linhas_markdown.extend(["", "## Ações Recomendadas"])
    for acao in acoes:
        linhas_markdown.append(f"- {acao}")

    markdown_relatorio = "\n".join(linhas_markdown)

    output_resumo_csv = io.StringIO()
    writer_resumo = csv.DictWriter(
        output_resumo_csv,
        fieldnames=["Indicador", "Valor"],
    )
    writer_resumo.writeheader()
    writer_resumo.writerow({"Indicador": "Periodo", "Valor": periodo_texto})
    writer_resumo.writerow({"Indicador": "Entradas", "Valor": perf["entradas"]})
    writer_resumo.writerow({"Indicador": "Conversoes_GANHO", "Valor": perf["ganhos"]})
    writer_resumo.writerow({"Indicador": "Taxa_conversao_percentual", "Valor": perf["taxa_conversao"]})
    writer_resumo.writerow({"Indicador": "Meta_mensal_percentual", "Valor": meta_conversao})
    writer_resumo.writerow({"Indicador": "Atingimento_meta_percentual", "Valor": atingimento})
    writer_resumo.writerow({"Indicador": "Gap_vs_meta_percentual", "Valor": gap_meta})
    writer_resumo.writerow({"Indicador": "SLA_critico_72h", "Valor": criticos_72h})
    writer_resumo.writerow({"Indicador": "SLA_atencao_48_71h", "Valor": atencao_48h})
    writer_resumo.writerow({"Indicador": "Etapa_mais_recorrente", "Valor": etapa_mais_frequente})
    writer_resumo.writerow({"Indicador": "Gargalo_etapa", "Valor": gargalo_etapa or ""})
    writer_resumo.writerow({"Indicador": "Gargalo_tempo_medio_horas", "Valor": maior_tempo})

    for idx, acao in enumerate(acoes, start=1):
        writer_resumo.writerow({"Indicador": f"Acao_recomendada_{idx}", "Valor": acao})

    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button(
            label="⬇️ Baixar Resumo (Markdown)",
            data=markdown_relatorio,
            file_name="resumo_executivo_comercial.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with ex2:
        st.download_button(
            label="⬇️ Baixar Resumo (CSV)",
            data=output_resumo_csv.getvalue(),
            file_name="resumo_executivo_comercial.csv",
            mime="text/csv",
            use_container_width=True,
        )

    etapas = perf.get("tempo_medio_etapas", [])
    if etapas:
        tabela_etapas = [
            {
                "Etapa (status)": e[0],
                "Tempo médio desde criação (h)": e[1],
            }
            for e in etapas
        ]
        st.dataframe(tabela_etapas, use_container_width=True)
        st.bar_chart(
            {
                row["Etapa (status)"]: [row["Tempo médio desde criação (h)"]]
                for row in tabela_etapas
            }
        )
    else:
        st.info("Sem movimentações suficientes no período para calcular tempo médio por etapa.")

    tabela_leads = [
        {
            "ID": l[0],
            "Nome": l[1],
            "Plano": l[2],
            "Status": l[3],
            "Email": l[4] or "",
            "WhatsApp": l[5] or "",
            "Cidade": l[6] or "",
            "UF": l[7] or "",
            "CNAE": l[8] or "",
            "Origem": l[9] or "",
            "Data": l[10],
        }
        for l in leads
    ]

    st.dataframe(tabela_leads, use_container_width=True)

    st.markdown("#### ✍️ Atualizar status de atendimento")
    if leads:
        mapa_leads = {f"#{l[0]} - {l[1]} ({l[3]})": l[0] for l in leads}
        c_up1, c_up2, c_up3, c_up4 = st.columns(4)
        with c_up1:
            lead_selecionado = st.selectbox("Selecionar lead", list(mapa_leads.keys()), key="lead_status_id")
        with c_up2:
            novo_status = st.selectbox(
                "Novo status",
                ["NOVO", "EM_CONTATO", "PROPOSTA_ENVIADA", "GANHO", "PERDIDO"],
                key="lead_status_novo",
            )
        with c_up3:
            st.text_input("Alterado por", value="Equipe Comercial", key="usuario_movimentacao")
        with c_up4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Salvar status", key="lead_status_salvar", use_container_width=True):
                lead_id = mapa_leads[lead_selecionado]
                alterados = atualizar_status_lead(
                    lead_id,
                    novo_status,
                    alterado_por=st.session_state.get("usuario_movimentacao", "Equipe Comercial"),
                    observacao=st.session_state.get("observacao_movimentacao", ""),
                )
                if alterados:
                    st.success("Status atualizado com sucesso.")
                    st.rerun()
                else:
                    st.warning("Nenhum registro foi atualizado.")

        st.text_area(
            "Observação da movimentação (opcional)",
            key="observacao_movimentacao",
            placeholder="Ex: Cliente pediu retorno na próxima semana.",
        )
    else:
        st.info("Sem leads para atualização no filtro atual.")

    st.markdown("#### 🕓 Histórico de movimentações")
    if leads:
        opcoes_historico = {"Todos os leads": None}
        for l in leads:
            opcoes_historico[f"#{l[0]} - {l[1]}"] = l[0]

        lead_historico_label = st.selectbox(
            "Filtrar histórico por lead",
            list(opcoes_historico.keys()),
            key="historico_lead_filtro",
        )
        lead_historico_id = opcoes_historico[lead_historico_label]
    else:
        lead_historico_id = None

    historico = carregar_historico_movimentacoes(lead_id=lead_historico_id, limite=50)
    if historico:
        tabela_historico = [
            {
                "Mov.": h[0],
                "Lead ID": h[1],
                "Nome": h[2],
                "Status anterior": h[3] or "",
                "Status novo": h[4],
                "Alterado por": h[5] or "",
                "Observação": h[6] or "",
                "Data": h[7],
            }
            for h in historico
        ]
        st.dataframe(tabela_historico, use_container_width=True)
    else:
        st.info("Ainda não há movimentações registradas para o filtro selecionado.")

    output_csv = io.StringIO()
    writer = csv.DictWriter(
        output_csv,
        fieldnames=["ID", "Nome", "Plano", "Status", "Email", "WhatsApp", "Cidade", "UF", "CNAE", "Origem", "Data"],
    )
    writer.writeheader()
    for row in tabela_leads:
        writer.writerow(row)

    st.download_button(
        label="📤 Exportar leads (CSV)",
        data=output_csv.getvalue(),
        file_name="leads_comerciais.csv",
        mime="text/csv",
        use_container_width=True,
    )

    output_historico_csv = io.StringIO()
    writer_hist = csv.DictWriter(
        output_historico_csv,
        fieldnames=["Mov.", "Lead ID", "Nome", "Status anterior", "Status novo", "Alterado por", "Observação", "Data"],
    )
    writer_hist.writeheader()
    if historico:
        for h in historico:
            writer_hist.writerow(
                {
                    "Mov.": h[0],
                    "Lead ID": h[1],
                    "Nome": h[2],
                    "Status anterior": h[3] or "",
                    "Status novo": h[4],
                    "Alterado por": h[5] or "",
                    "Observação": h[6] or "",
                    "Data": h[7],
                }
            )

    pacote_zip = io.BytesIO()
    with zipfile.ZipFile(pacote_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("resumo_executivo_comercial.md", markdown_relatorio)
        zf.writestr("resumo_executivo_comercial.csv", output_resumo_csv.getvalue())
        zf.writestr("leads_filtrados.csv", output_csv.getvalue())
        zf.writestr("historico_movimentacoes.csv", output_historico_csv.getvalue())
    pacote_zip.seek(0)

    timestamp_relatorio = datetime.now().strftime("%Y%m%d_%H%M%S")

    st.download_button(
        label="📦 Baixar Pacote Completo (ZIP)",
        data=pacote_zip.getvalue(),
        file_name=f"pacote_relatorios_comercial_{timestamp_relatorio}.zip",
        mime="application/zip",
        use_container_width=True,
    )

    st.info("Fluxo completo ativo: filtre, atualize status e exporte CSV, resumo e pacote ZIP para o comercial.")
