import streamlit as st
import sqlite3
import os
import json
import unicodedata

from config_banco import conectar_banco as abrir_banco, obter_caminho_banco, LEGACY_DB

# Importa o motor de busca inteligente por CNAE
from engine_busca import api_enquadramento_avancado
import core.painel_helpers as painel_helpers
from core.sidebar_flow import montar_filtro_consulta_livre
from core.tela4_leads import render_tela4_gestao_leads
from core.tela3_planos import render_tela3_planos_precos
from core.consulta_instrumento_service import buscar_retorno_por_instrumento
from core.tela2_dashboard import render_tela2_dashboard_complexo

normalizar_texto = getattr(
    painel_helpers,
    "normalizar_texto",
    lambda texto: "".join(
        c for c in unicodedata.normalize("NFD", str(texto or "")) if unicodedata.category(c) != "Mn"
    ).upper().strip(),
)
inferir_abrangencia_cct = getattr(
    painel_helpers,
    "inferir_abrangencia_cct",
    lambda arquivo_origem, abrangencia_atual="": abrangencia_atual or "Não Informada",
)
inferir_titulo_cct = getattr(
    painel_helpers,
    "inferir_titulo_cct",
    lambda _arquivo_origem, vigencia_inicio="", vigencia_fim="": f"Convenção Coletiva {vigencia_inicio}-{vigencia_fim}".strip("-"),
)
resolver_entidades_cct = getattr(
    painel_helpers,
    "resolver_entidades_cct",
    lambda patronal, laboral, _arquivo: (patronal or "Não Informado", laboral or "Não Informado"),
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOGO_NEW_RESULTS = os.path.join(BASE_DIR, "Logo New Results.jpg")

# Configuração da página
st.set_page_config(page_title="Automação de Gestão Sindical", layout="wide", page_icon="⚖️")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&display=swap');

    :root {
        --dola-azul-escuro: #0A2463;
        --dola-azul-claro: #3E92CC;
        --dola-fundo: #F4F8FC;
        --dola-ink: #102242;
    }

    html, body, [class*="css"]  {
        font-family: 'Manrope', sans-serif;
        color: var(--dola-ink);
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 8%, rgba(62,146,204,0.22), transparent 40%),
            radial-gradient(circle at 92% 12%, rgba(10,36,99,0.18), transparent 34%),
            linear-gradient(180deg, #FFFFFF 0%, var(--dola-fundo) 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10,36,99,0.95), rgba(11,53,128,0.95));
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [role="combobox"],
    [data-testid="stSidebar"] [data-baseweb="select"] input,
    [data-testid="stSidebar"] [data-baseweb="base-input"] input,
    [data-testid="stSidebar"] [data-baseweb="input"] input {
        color: var(--dola-ink) !important;
        -webkit-text-fill-color: var(--dola-ink) !important;
        caret-color: var(--dola-ink) !important;
        background: #FFFFFF !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] svg,
    [data-testid="stSidebar"] [data-baseweb="base-input"] svg,
    [data-testid="stSidebar"] button[kind="secondary"] svg {
        fill: var(--dola-ink) !important;
        color: var(--dola-ink) !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--dola-azul-escuro);
        font-weight: 800;
        font-size: clamp(1rem, 1.15vw, 1.45rem);
        line-height: 1.2;
        white-space: normal;
        overflow-wrap: anywhere;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem;
    }

    .stButton > button {
        background: linear-gradient(90deg, var(--dola-azul-escuro), var(--dola-azul-claro));
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
    }

    .pricing-card {
        border-radius: 16px;
        padding: 18px;
        min-height: 300px;
        border: 1px solid #D0E2F2;
        background: linear-gradient(180deg, #FFFFFF, #F8FBFF);
        box-shadow: 0 8px 24px rgba(10,36,99,0.08);
    }

    .pricing-card.recommended {
        border: 2px solid #3E92CC;
        box-shadow: 0 10px 30px rgba(62,146,204,0.25);
        transform: translateY(-4px);
    }

    .pricing-badge {
        display: inline-block;
        background: #3E92CC;
        color: #FFFFFF;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .pricing-price {
        font-size: 34px;
        font-weight: 800;
        color: #0A2463;
        line-height: 1.1;
        margin: 6px 0 10px 0;
    }

    .pricing-sub {
        color: #334155;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def garantir_clientes_escritorio(cursor_principal):
    """Garante a tabela de clientes do escritorio e sincroniza do legado se necessario."""
    cursor_principal.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes_escritorio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_empresa TEXT,
            situacao TEXT,
            apelido TEXT,
            razao_social TEXT,
            cnpj TEXT,
            cnae TEXT,
            nome_sindicato TEXT,
            codigo_sindicato TEXT,
            data_base TEXT
        )
        """
    )

    total_atual = cursor_principal.execute("SELECT COUNT(*) FROM clientes_escritorio").fetchone()[0]
    banco_atual = os.path.abspath(obter_caminho_banco())
    banco_legado = os.path.abspath(LEGACY_DB)

    if total_atual > 0 or banco_atual == banco_legado or not os.path.exists(banco_legado):
        return

    conn_legado = sqlite3.connect(banco_legado)
    cursor_legado = conn_legado.cursor()
    tabela_legado = cursor_legado.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='clientes_escritorio'"
    ).fetchone()[0]

    if tabela_legado:
        linhas_legado = cursor_legado.execute(
            """
            SELECT codigo_empresa, situacao, apelido, razao_social, cnpj, cnae,
                   nome_sindicato, codigo_sindicato, data_base
            FROM clientes_escritorio
            """
        ).fetchall()
        if linhas_legado:
            cursor_principal.executemany(
                """
                INSERT INTO clientes_escritorio (
                    codigo_empresa, situacao, apelido, razao_social, cnpj, cnae,
                    nome_sindicato, codigo_sindicato, data_base
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                linhas_legado,
            )

    conn_legado.close()


def carregar_clientes_sidebar(cursor_principal):
    """Retorna clientes do escritorio; se ausentes, faz fallback apenas para entidades EMPRESA."""
    cursor_principal.execute(
        """
        SELECT apelido, razao_social, cnpj, cnae, nome_sindicato, codigo_sindicato, data_base
        FROM clientes_escritorio
        WHERE COALESCE(situacao, 'Ativas') = 'Ativas'
        ORDER BY COALESCE(apelido, ''), razao_social
        """
    )
    clientes_escritorio = cursor_principal.fetchall()
    if clientes_escritorio:
        return "clientes_escritorio", clientes_escritorio

    cursor_principal.execute(
        """
        SELECT nome_fantasia, razao_social, cnpj, categoria_principal, tipo, municipio, uf
        FROM entidades
        WHERE ativo = 1
          AND UPPER(COALESCE(tipo, '')) = 'EMPRESA'
        ORDER BY nome_fantasia, razao_social
        """
    )
    return "entidades_empresa", cursor_principal.fetchall()


def normalizar_ccts_legadas(cursor_principal):
    """Corrige registros de CCT importados com placeholders genéricos."""
    cursor_principal.execute(
        """
        SELECT id, arquivo_origem, id_entidade_patronal, id_entidade_sindical,
               vigencia_inicio, vigencia_fim, abrangencia_territorial, titulo, dados_completos
        FROM ccts
        """
    )
    atualizacoes = []

    for linha in cursor_principal.fetchall():
        cct_id, arquivo_origem, patronal_atual, laboral_atual, vigencia_inicio, vigencia_fim, abrangencia_atual, titulo_atual, dados_completos = linha
        patronal_novo, laboral_novo = resolver_entidades_cct(patronal_atual, laboral_atual, arquivo_origem)
        abrangencia_nova = inferir_abrangencia_cct(arquivo_origem, abrangencia_atual)
        titulo_novo = titulo_atual or inferir_titulo_cct(arquivo_origem, vigencia_inicio, vigencia_fim)

        dados_completos_novo = dados_completos
        if dados_completos:
            try:
                payload = json.loads(dados_completos)
                payload["id_entidade_patronal"] = patronal_novo
                payload["id_entidade_sindical"] = laboral_novo
                payload["abrangencia_territorial"] = abrangencia_nova
                payload["titulo"] = titulo_novo
                dados_completos_novo = json.dumps(payload, ensure_ascii=False)
            except Exception:
                dados_completos_novo = dados_completos

        if (
            patronal_novo != (patronal_atual or "")
            or laboral_novo != (laboral_atual or "")
            or abrangencia_nova != (abrangencia_atual or "")
            or titulo_novo != (titulo_atual or "")
            or dados_completos_novo != (dados_completos or "")
        ):
            atualizacoes.append((
                patronal_novo,
                laboral_novo,
                abrangencia_nova,
                titulo_novo,
                dados_completos_novo,
                cct_id,
            ))

    if atualizacoes:
        cursor_principal.executemany(
            """
            UPDATE ccts
            SET id_entidade_patronal = ?,
                id_entidade_sindical = ?,
                abrangencia_territorial = ?,
                titulo = ?,
                dados_completos = ?
            WHERE id = ?
            """,
            atualizacoes,
        )

# --- INICIALIZAÇÃO E MIGRAÇÃO AUTOMÁTICA DE BANCO ---
conn = abrir_banco()
cursor = conn.cursor()
garantir_clientes_escritorio(cursor)

# Garante a existência das tabelas estruturadas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS entidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_fantasia TEXT,
        razao_social TEXT,
        cnpj TEXT,
        categoria_principal TEXT,
        tipo TEXT,
        ativo INTEGER
    );
""")
try: cursor.execute("ALTER TABLE entidades ADD COLUMN tipo TEXT;")
except sqlite3.OperationalError: pass
try: cursor.execute("ALTER TABLE entidades ADD COLUMN ativo INTEGER DEFAULT 1;")
except sqlite3.OperationalError: pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ccts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arquivo_origem TEXT UNIQUE,
        id_entidade_patronal TEXT,
        id_entidade_sindical TEXT,
        vigencia_inicio TEXT,
        vigencia_fim TEXT,
        abrangencia_territorial TEXT,
        titulo TEXT,
        piso_salarial TEXT,
        clausula_critica TEXT,
        dados_completos TEXT
    );
""")

colunas_necessarias_ccts = [
    ("arquivo_origem", "TEXT"), ("id_entidade_patronal", "TEXT"), ("id_entidade_sindical", "TEXT"),
    ("vigencia_inicio", "TEXT"), ("vigencia_fim", "TEXT"), ("abrangencia_territorial", "TEXT"),
    ("titulo", "TEXT"), ("piso_salarial", "TEXT"), ("clausula_critica", "TEXT"), ("dados_completos", "TEXT")
]
for col, tipo in colunas_necessarias_ccts:
    try: cursor.execute(f"ALTER TABLE ccts ADD COLUMN {col} {tipo};")
    except sqlite3.OperationalError: pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads_comerciais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        whatsapp TEXT,
        plano_interesse TEXT NOT NULL,
        status_atendimento TEXT DEFAULT 'NOVO',
        origem_tela TEXT,
        cidade_contexto TEXT,
        uf_contexto TEXT,
        cnae_contexto TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
try: cursor.execute("ALTER TABLE leads_comerciais ADD COLUMN status_atendimento TEXT DEFAULT 'NOVO';")
except sqlite3.OperationalError: pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads_movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        status_anterior TEXT,
        status_novo TEXT NOT NULL,
        alterado_por TEXT,
        observacao TEXT,
        data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads_comerciais(id)
    );
""")

normalizar_ccts_legadas(cursor)
conn.commit()

# Consulta total de registros salvos para auditoria visual rápida
cursor.execute("SELECT COUNT(*) FROM ccts")
total_ccts_banco = cursor.fetchone()[0]

# --- BARRA LATERAL (INTEGRAÇÃO COMERCIAL) ---
if os.path.exists(CAMINHO_LOGO_NEW_RESULTS):
    st.sidebar.image(CAMINHO_LOGO_NEW_RESULTS, use_container_width=True)
st.sidebar.markdown("## ⚖️")
st.sidebar.title("🔍 Central de Consultas")
st.sidebar.caption(f"📊 Total no Banco: {total_ccts_banco} documento(s)")

tipo_busca = st.sidebar.radio(
    "Escolha o Modo de Navegação:",
    ["Por Empresa (Minha Carteira)", "Consulta Livre (Produto SaaS)"],
    key="modo_navegacao",
)
st.sidebar.caption(f"Modo ativo: {tipo_busca}")

tela_dashboard = st.sidebar.selectbox(
    "Layout do Dashboard",
    [
        "Tela 1 • Dashboard Simples (CNAE)",
        "Tela 2 • Dashboard Complexo (CNAE + Cargos)",
        "Tela 3 • Planos e Preços",
        "Tela 4 • Gestão de Leads",
    ],
)

empresa_selecionada = None
filtro_manual = None
funcionarios_para_analise = []

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Simulador de Impacto")
qtd_funcionarios_sim = st.sidebar.number_input("Funcionários na base", min_value=1, value=25, step=1)
salario_base_informado = st.sidebar.number_input("Salário atual (referência)", min_value=0.0, value=1890.0, step=50.0)
faturamento_mensal_sim = st.sidebar.number_input("Faturamento mensal (opcional)", min_value=0.0, value=0.0, step=1000.0)
usar_piso_cct = st.sidebar.checkbox("Usar piso da CCT como base automática", value=True)
inflacao_base_sim = st.sidebar.number_input("Inflação de referência (%)", min_value=0.0, value=4.52, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Comportamento")
auto_atualizar_consulta = st.sidebar.checkbox("Atualizar painel automaticamente", value=True)
mostrar_modo_dev = st.sidebar.checkbox("Exibir Modo Desenvolvedor", value=False)

if tipo_busca == "Por Empresa (Minha Carteira)":
    st.sidebar.subheader("Selecione o Cliente")

    origem_clientes, lista_clientes = carregar_clientes_sidebar(cursor)
    
    opcoes_clientes = [f"{c[0] or 'Sem nome'} - {c[1][:30]}..." for c in lista_clientes]
    
    if opcoes_clientes:
        escolha = st.sidebar.selectbox("Buscar por Nome Fantasia/Razão:", opcoes_clientes)
        index = opcoes_clientes.index(escolha)
        dados_emp = lista_clientes[index]

        if origem_clientes == "clientes_escritorio":
            empresa_selecionada = {
                "razao_social": dados_emp[1],
                "apelido": dados_emp[0],
                "cnpj": dados_emp[2],
                "cnae": dados_emp[3] or "6920601",
                "modo": "empresa",
                "tipo": "CLIENTE_ESCRITORIO",
                "cidade": "MARINGA",
                "uf": "PR",
                "nome_sindicato": dados_emp[4] or "",
                "codigo_sindicato": dados_emp[5] or "",
                "data_base": dados_emp[6] or "",
            }
        else:
            empresa_selecionada = {
                "razao_social": dados_emp[1],
                "apelido": dados_emp[0],
                "cnpj": dados_emp[2],
                "cnae": dados_emp[3] or "6920601",
                "modo": "empresa",
                "tipo": dados_emp[4] or "DESCONHECIDO",
                "cidade": dados_emp[5] or "MARINGA",
                "uf": dados_emp[6] or "PR"
            }

        st.sidebar.markdown("---")
        st.sidebar.caption("Análise avançada opcional por cargos/CBO")
        entrada_cargos = st.sidebar.text_area(
            "Cargos e CBO (1 por linha)",
            placeholder="Motorista|7823\nVigilante|5173\nAuxiliar Administrativo|",
            help="Formato: Cargo|CBO. O CBO é opcional.",
        )

        if entrada_cargos:
            for i, linha in enumerate(entrada_cargos.splitlines(), start=1):
                texto = linha.strip()
                if not texto:
                    continue
                partes = [p.strip() for p in texto.split("|", 1)]
                cargo = partes[0] if partes else ""
                cbo = partes[1] if len(partes) > 1 else ""
                funcionarios_para_analise.append(
                    {
                        "id": i,
                        "nome": f"Funcionario {i}",
                        "cargo": cargo,
                        "cbo": cbo,
                    }
                )
    else:
        st.sidebar.warning("Nenhum cliente do escritório encontrado no banco.")

else:
    try:
        filtro_manual = montar_filtro_consulta_livre(cursor, normalizar_texto)
    except Exception as e:
        st.sidebar.error(f"Erro ao montar fluxo de enquadramento: {e}")
        filtro_manual = None


consulta_livre_pronta = bool(
    filtro_manual
    and filtro_manual.get("uf")
    and filtro_manual.get("cidade")
    and filtro_manual.get("sindicato")
    and filtro_manual.get("instrumento")
)

if tipo_busca == "Consulta Livre (Produto SaaS)" and not consulta_livre_pronta:
    st.sidebar.caption("Complete UF, cidade, sindicato e instrumento para habilitar a consulta.")

conn.close()

btn_consultar = st.sidebar.button(
    "🚀 Cruzar Dados e Exibir",
    use_container_width=True,
    disabled=tipo_busca == "Consulta Livre (Produto SaaS)" and not consulta_livre_pronta,
)
executar_consulta = btn_consultar or auto_atualizar_consulta

# --- LÓGICA DE CRUZAMENTO E RENDERIZAÇÃO DA TELA CENTRAL ---
if executar_consulta:
    retorno_motor = None
    diagnostico_cargos = None
    cidade, uf = "Não Identificada", "PR"

    if tela_dashboard.startswith("Tela 4"):
        render_tela4_gestao_leads()
        st.stop()

    if tipo_busca == "Por Empresa (Minha Carteira)" and empresa_selecionada:
        st.markdown(f"### 🏢 Empresa Identificada: **{empresa_selecionada['razao_social']}**")
        st.caption(f"**CNAE Detectado:** {empresa_selecionada['cnae']} | **CNPJ:** {empresa_selecionada['cnpj']}")
        cidade = empresa_selecionada.get("cidade", "MARINGA")
        uf = empresa_selecionada.get("uf", "PR")

        retorno_avancado = api_enquadramento_avancado(
            empresa_selecionada['cnae'],
            cidade,
            uf,
            funcionarios=funcionarios_para_analise,
        )
        retorno_motor = {
            "principais": retorno_avancado.get("principais", []),
            "satelites": retorno_avancado.get("satelites", []),
        }
        diagnostico_cargos = retorno_avancado.get("diagnostico_cargos")

    elif tipo_busca == "Consulta Livre (Produto SaaS)" and filtro_manual:
        if consulta_livre_pronta:
            cidade, uf = filtro_manual['cidade'], filtro_manual['uf']
            st.markdown(f"### 🌍 Consulta Regional: **{cidade} - {uf}**")

            instrumento = filtro_manual.get("instrumento")
            retorno_motor = buscar_retorno_por_instrumento(instrumento)
        else:
            st.info("Selecione estado, cidade, sindicato e instrumento coletivo para executar a consulta livre.")
            st.stop()

    if retorno_motor and (retorno_motor["principais"] or retorno_motor["satelites"]):
        st.markdown(f"##### Base Territorial da Operação: **{cidade} - {uf}**")
        st.write("---")
        st.markdown("#### 🛡️ Processando Pilar 2: Consultando Banco de Dados Relacional")
        st.success("✅ SUCESSO: Registros localizados e mapeados com precisão!")

        if tela_dashboard.startswith("Tela 1"):
            cct_unica = None
            if retorno_motor["principais"]:
                cct_unica = retorno_motor["principais"][0]
            elif retorno_motor["satelites"]:
                cct_unica = retorno_motor["satelites"][0]

            st.markdown("### 📊 Tela 1: Enquadramento Único por CNAE")

            if cct_unica:
                cnae_em_uso = "Não informado"
                if empresa_selecionada:
                    cnae_em_uso = empresa_selecionada.get("cnae", "Não informado")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("CNAE analisado", cnae_em_uso)
                with c2:
                    st.metric("Vigência", cct_unica.get("vigencia", "Não informado"))
                with c3:
                    st.metric("Piso salarial", cct_unica.get("piso", "Não informado"))
                with c4:
                    st.metric("Reajuste", cct_unica.get("reajuste", "Não informado"))

                st.info(
                    f"🏢 Patronal: {cct_unica.get('patronal', 'Não informado')}\n\n"
                    f"🤝 Laboral: {cct_unica.get('laboral', 'Não informado')}"
                )

                st.markdown("#### 🧾 Resumo Técnico da CCT Selecionada")
                st.dataframe(
                    [
                        {
                            "Tipo": "Principal" if retorno_motor["principais"] else "Satélite",
                            "Patronal": cct_unica.get("patronal", ""),
                            "Laboral": cct_unica.get("laboral", ""),
                            "Vigência": cct_unica.get("vigencia", ""),
                            "Piso": cct_unica.get("piso", ""),
                            "Reajuste": cct_unica.get("reajuste", ""),
                            "Cidade": cidade,
                            "UF": uf,
                        }
                    ],
                    use_container_width=True,
                )

                st.caption("Modo simplificado ativo: exibindo um enquadramento consolidado por CNAE.")
            else:
                st.warning("Nenhuma CCT foi localizada para o cenário atual.")

            st.stop()

        if tela_dashboard.startswith("Tela 3"):
            render_tela3_planos_precos(
                empresa_selecionada=empresa_selecionada,
                cidade=cidade,
                uf=uf,
            )

            st.stop()

        render_tela2_dashboard_complexo(
            retorno_motor=retorno_motor,
            diagnostico_cargos=diagnostico_cargos,
            salario_base_informado=salario_base_informado,
            usar_piso_cct=usar_piso_cct,
            qtd_funcionarios_sim=qtd_funcionarios_sim,
            faturamento_mensal_sim=faturamento_mensal_sim,
            inflacao_base_sim=inflacao_base_sim,
        )
    else:
        st.write("---")
        st.markdown("#### 🛡️ Processando Pilar 2: Consultando Banco de Dados Relacional")
        st.error("❌ Atenção: Nenhuma Convenção Coletiva (CCT) correspondente foi localizada no banco para este cenário.")

# --- BOX INFORMATIVO DE DIAGNÓSTICO (Opcional) ---
if mostrar_modo_dev:
    with st.expander("🛠️ Modo Desenvolvedor: Visualizar Listagem Bruta do Banco"):
        st.caption("Abaixo estão listadas CCTs deduplicadas para auditoria rápida.")
        try:
            conn = abrir_banco()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id_entidade_patronal, id_entidade_sindical, abrangencia_territorial, COUNT(*)
                FROM ccts
                GROUP BY id_entidade_patronal, id_entidade_sindical, abrangencia_territorial
                ORDER BY COUNT(*) DESC, id_entidade_patronal
                LIMIT 100
                """
            )
            linhas = cursor.fetchall()
            conn.close()

            if linhas:
                tabela_dev = [
                    {
                        "Patronal": l[0] or "",
                        "Laboral": l[1] or "",
                        "Abrangência": l[2] or "",
                        "Ocorrências": l[3],
                    }
                    for l in linhas
                ]
                st.dataframe(tabela_dev, use_container_width=True)
            else:
                st.info("Sem registros em ccts para exibir no modo desenvolvedor.")
        except Exception as e:
            st.text(f"Não foi possível ler os dados brutos: {e}")