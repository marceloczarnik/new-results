import streamlit as st

from core.calculos_basicos import CalculosBasicos
from core.impacto_financeiro import NucleoNegociacao
from core.painel_helpers import extrair_valor_monetario, extrair_percentual, classificar_alerta
from core.ui_components import render_alerta_colorido, renderizar_card_cct


def render_tela2_dashboard_complexo(
    retorno_motor,
    diagnostico_cargos,
    salario_base_informado,
    usar_piso_cct,
    qtd_funcionarios_sim,
    faturamento_mensal_sim,
    inflacao_base_sim,
):
    """Renderiza a Tela 2 com cruzamento CNAE + Cargos e impacto financeiro."""
    st.markdown("### 🧠 Tela 2: Dashboard Complexo (CNAE + Cargos)")

    # Módulos 4 e 5: Cálculo de impacto financeiro com base na CCT.
    cct_base = None
    if retorno_motor["principais"]:
        cct_base = retorno_motor["principais"][0]
    elif retorno_motor["satelites"]:
        cct_base = retorno_motor["satelites"][0]

    if cct_base:
        piso_detectado = extrair_valor_monetario(cct_base.get("piso"))
        reajuste_detectado = extrair_percentual(cct_base.get("reajuste"))

        salario_base_calculo = salario_base_informado
        if usar_piso_cct and piso_detectado > 0:
            salario_base_calculo = piso_detectado

        calc = CalculosBasicos()
        salario_reajustado = calc.calcular_valor_com_reajuste(salario_base_calculo, reajuste_detectado)

        nucleo = NucleoNegociacao()
        resultado_impacto = nucleo.calcular_impacto_completo(
            valor_atual=salario_base_calculo,
            valor_reajustado=salario_reajustado,
            quantidade_funcionarios=int(qtd_funcionarios_sim),
            faturamento_mensal_empresa=float(faturamento_mensal_sim) if faturamento_mensal_sim > 0 else None,
        )

        percentual_pessimista = inflacao_base_sim
        percentual_moderado = max(inflacao_base_sim, reajuste_detectado)
        percentual_otimista = percentual_moderado + 1.5

        cenarios = [
            ("📉 Pessimista", percentual_pessimista),
            ("⚖️ Moderado", percentual_moderado),
            ("📈 Otimista", percentual_otimista),
        ]

        tabela_cenarios = []
        for nome_cenario, percentual in cenarios:
            salario_cenario = calc.calcular_valor_com_reajuste(salario_base_calculo, percentual)
            impacto_cenario = nucleo.calcular_impacto_completo(
                valor_atual=salario_base_calculo,
                valor_reajustado=salario_cenario,
                quantidade_funcionarios=int(qtd_funcionarios_sim),
                faturamento_mensal_empresa=float(faturamento_mensal_sim) if faturamento_mensal_sim > 0 else None,
            )
            tabela_cenarios.append(
                {
                    "Cenario": nome_cenario,
                    "Reajuste (%)": round(percentual, 2),
                    "Salario Reajustado": round(salario_cenario, 2),
                    "Impacto Mensal": round(impacto_cenario["impacto_aumento"]["valor_mensal"], 2),
                    "Impacto Anual": round(impacto_cenario["impacto_aumento"]["valor_anual"], 2),
                }
            )

        st.write("---")
        st.markdown("### 🚨 Diferenciais e Alertas Prioritários")

        alertas_detectados = []
        for cct in (retorno_motor.get("principais", []) + retorno_motor.get("satelites", [])):
            critica = cct.get("critica")
            if critica and "nenhuma" not in str(critica).lower():
                alertas_detectados.append(
                    {
                        "nivel": classificar_alerta(critica),
                        "mensagem": critica,
                        "origem": cct.get("patronal", "CCT"),
                    }
                )

        if alertas_detectados:
            st.error("⚠️ Alertas relevantes detectados no cruzamento de CCTs.")
            for alerta in alertas_detectados[:4]:
                render_alerta_colorido(
                    alerta["nivel"],
                    f"{alerta['mensagem']} (Origem: {alerta['origem']})",
                )
        else:
            st.success("✅ Nenhuma cláusula crítica explícita foi detectada no recorte atual.")

        sindicatos_sugeridos = []
        detalhes_funcionarios = []
        if diagnostico_cargos:
            sindicatos_sugeridos = diagnostico_cargos.get("sindicatos_satelites_obrigatorios", [])
            detalhes_funcionarios = diagnostico_cargos.get("detalhe_funcionarios_especiais", [])

        if sindicatos_sugeridos:
            st.warning("🛰️ Satélites sugeridos por CNAE + Cargos: " + ", ".join(sindicatos_sugeridos))
        else:
            st.info("ℹ️ Sem novos satélites sugeridos pela análise de cargos/CBO.")

        if diagnostico_cargos:
            c_cross_1, c_cross_2, c_cross_3 = st.columns(3)
            with c_cross_1:
                st.metric(
                    "Funcionários analisados",
                    diagnostico_cargos.get("total_funcionarios_analisados", 0),
                )
            with c_cross_2:
                st.metric(
                    "Categorias especiais",
                    diagnostico_cargos.get("total_categorias_especiais_encontradas", 0),
                )
            with c_cross_3:
                st.metric("Satélites identificados", len(sindicatos_sugeridos))

        st.write("---")
        st.markdown("### 💸 Impacto Financeiro da CCT (Módulos 4 e 5)")
        st.caption(
            f"Base usada: R$ {salario_base_calculo:,.2f} | Reajuste aplicado: {reajuste_detectado:.2f}% | "
            f"Funcionários: {int(qtd_funcionarios_sim)}"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Custo mensal atual", f"R$ {resultado_impacto['custo_atual']['custo_total_mensal']:,.2f}")
        with c2:
            st.metric("Custo mensal projetado", f"R$ {resultado_impacto['custo_projetado']['custo_total_mensal']:,.2f}")
        with c3:
            st.metric("Impacto mensal", f"R$ {resultado_impacto['impacto_aumento']['valor_mensal']:,.2f}")

        st.info(f"Impacto anual estimado: R$ {resultado_impacto['impacto_aumento']['valor_anual']:,.2f}")

        st.bar_chart(
            {
                "Custo Atual": [resultado_impacto["custo_atual"]["custo_total_mensal"]],
                "Custo Projetado": [resultado_impacto["custo_projetado"]["custo_total_mensal"]],
            }
        )

        tabela_impacto = [
            {
                "Cenario": "Atual",
                "Salario Unitario": round(salario_base_calculo, 2),
                "Custo Mensal Total": round(resultado_impacto["custo_atual"]["custo_total_mensal"], 2),
                "Custo Anual Total": round(resultado_impacto["custo_atual"]["custo_total_anual"], 2),
            },
            {
                "Cenario": "Projetado",
                "Salario Unitario": round(salario_reajustado, 2),
                "Custo Mensal Total": round(resultado_impacto["custo_projetado"]["custo_total_mensal"], 2),
                "Custo Anual Total": round(resultado_impacto["custo_projetado"]["custo_total_anual"], 2),
            },
        ]
        st.dataframe(tabela_impacto, use_container_width=True)

        st.markdown("#### 📌 Cenários de Negociação")
        st.dataframe(tabela_cenarios, use_container_width=True)
        st.bar_chart(
            {
                item["Cenario"]: [item["Impacto Mensal"]]
                for item in tabela_cenarios
            }
        )

        capacidade = resultado_impacto.get("capacidade_economica", {})
        if capacidade:
            st.warning(
                f"Capacidade econômica: atual {capacidade.get('classificacao_atual', 'N/A')} | "
                f"após reajuste {capacidade.get('classificacao_nova', 'N/A')}"
            )

        st.write("---")
        st.markdown("### 🧾 Dados Técnicos da CCT")

        comparativo_ccts = []
        for cct in retorno_motor.get("principais", []):
            comparativo_ccts.append(
                {
                    "Tipo": "Principal",
                    "Patronal": cct.get("patronal", ""),
                    "Laboral": cct.get("laboral", ""),
                    "Piso": cct.get("piso", ""),
                    "Reajuste": cct.get("reajuste", ""),
                    "Vigência": cct.get("vigencia", ""),
                    "Risco": classificar_alerta(cct.get("critica", "")),
                }
            )
        for cct in retorno_motor.get("satelites", []):
            comparativo_ccts.append(
                {
                    "Tipo": "Satélite",
                    "Patronal": cct.get("patronal", ""),
                    "Laboral": cct.get("laboral", ""),
                    "Piso": cct.get("piso", ""),
                    "Reajuste": cct.get("reajuste", ""),
                    "Vigência": cct.get("vigencia", ""),
                    "Risco": classificar_alerta(cct.get("critica", "")),
                }
            )

        st.markdown("#### ⚖️ Quadro Comparativo: Principal vs Satélites")
        st.dataframe(comparativo_ccts, use_container_width=True)

        col_principal, col_satelite = st.columns([0.65, 0.35])
        with col_principal:
            st.markdown("#### 🏆 CCT Principal OBRIGATÓRIA")
            if retorno_motor["principais"]:
                for cct in retorno_motor["principais"]:
                    renderizar_card_cct(cct)
            else:
                st.info("ℹ️ Nenhuma CCT Principal vinculada diretamente a este CNAE.")

        with col_satelite:
            st.markdown("#### 🛰️ CCTs Satélites (Regras de Extensão)")
            if retorno_motor["satelites"]:
                for cct in retorno_motor["satelites"]:
                    with st.expander(f"📦 {cct['patronal'][:25]}...", expanded=True):
                        renderizar_card_cct(cct)
            else:
                st.info("ℹ️ Nenhuma CCT Satélite aplicável para esta operação.")

        if detalhes_funcionarios:
            st.markdown("#### 🔬 Detalhamento de Funcionários Enquadrados")
            st.dataframe(detalhes_funcionarios, use_container_width=True)
