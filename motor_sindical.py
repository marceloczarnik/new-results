import sys
import requests

# ==========================================
# ENGRENAGEM 2: BANCO DE DADOS DA MATRIZ SINDICAL
# ==========================================
MATRIZ_SINDICAL_DB = [
    {
        "cnae": "4712100",  # Comércio Varejista / Supermercados
        "uf": "SP",
        "municipio": "CAMPINAS",
        "cnpj_patronal": "99.888.777/0001-11",
        "cnpj_laboral": "55.666.777/0001-88",
        "categoria": "GERAL",
    },
   {
        "cnae": "6021700",  # CNAE da Globo (Televisão aberta)
        "uf": "RJ",
        "municipio": "RIO DE JANEIRO",
        "cnpj_patronal": "00.111.222/0001-33",  # CNPJ fictício do Sindicato das Empresas de TV
        "cnpj_laboral": "44.555.666/0001-77",  # CNPJ fictício do Sindicato dos Radialistas/Jornalistas RJ
        "categoria": "GERAL",
    }, 
]


# ==========================================
# ENGRENAGEM 1: BUSCA E HIGIENIZAÇÃO DO CNPJ
# ==========================================
def consultar_e_estruturar_cnpj(cnpj_usuario):
    cnpj_limpo = "".join(filter(str.isdigit, cnpj_usuario))

    if len(cnpj_limpo) != 14:
        print("❌ ERRO: CNPJ deve conter 14 dígitos.")
        return None

    print(f"🔍 Sincronizando dados com a Receita Federal para: {cnpj_usuario}...")

    # URL da API
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"

    # Adicionamos um "User-Agent" para simular um navegador comum e evitar bloqueios na API
    cabecalhos = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=cabecalhos, timeout=15)

        # Se a API rejeitar ou estiver instável
        if response.status_code != 200:
            print(
                f"❌ ERRO: O servidor da API respondeu com o código de status: {response.status_code}"
            )
            print(
                "Aguarde alguns segundos e tente rodar novamente (a API pública pode estar instável)."
            )
            return None

        dados = response.json()

        # Estrutura os dados dinâmicos da empresa
        return {
            "cnpj": dados.get("cnpj"),
            "razao_social": dados.get("razao_social"),
            "cnae_principal": str(dados.get("cnae_fiscal")),
            "cidade": dados.get("municipio").upper(),
            "uf": dados.get("uf").upper(),
        }

    except requests.exceptions.JSONDecodeError:
        print(
            "❌ ERRO: A API retornou uma resposta inválida (Provável instabilidade no servidor deles)."
        )
        return None
    except Exception as e:
        print(f"❌ ERRO de conexão inesperado: {e}")
        return None


# ==========================================
# RE-ENQUADRAMENTO SINDICAL AUTOMÁTICO
# ==========================================
def processar_enquadramento(empresa):
    if not empresa:
        return

    print("\n--- 🏢 DADOS DA EMPRESA LOCALIZADOS ---")
    print(f"Razão Social: {empresa['razao_social']}")
    print(f"Atividade (CNAE): {empresa['cnae_principal']}")
    print(f"Localização: {empresa['cidade']} - {empresa['uf']}")

    # Varre a matriz em busca do match exato
    for regra in MATRIZ_SINDICAL_DB:
        if (
            regra["cnae"] == empresa["cnae_principal"]
            and regra["uf"] == empresa["uf"]
            and regra["municipio"] == empresa["cidade"]
        ):
            print("\n--- ⚖️ ENQUADRAMENTO SINDICAL ENCONTRADO ---")
            print(f"Sindicato Patronal (Empresas): {regra['cnpj_patronal']}")
            print(f"Sindicato Laboral (Trabalhadores): {regra['cnpj_laboral']}")
            return

    print("\n⚠️ AVISO: Empresa ativa, mas sindicato ainda não mapeado nesta região.")


# ==========================================
# 🧪 TESTE REAL DO SISTEMA
# ==========================================
cnpj_teste = "27.865.757/0001-02"
dados_da_empresa = consultar_e_estruturar_cnpj(cnpj_teste)
processar_enquadramento(dados_da_empresa)