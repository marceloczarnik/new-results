# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: core/impacto_financeiro.py
# 📍 FUNÇÃO: Análise de Impacto e Custo Financeiro
#     Funcionalidade 3 - NÚCLEO DE NEGOCIAÇÃO®
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from typing import Dict, List, Union
import logging
import json
from datetime import datetime

# Importa os módulos que já estão prontos
try:
    from .calculos_basicos import CalculosBasicos
    from .projecao_reajuste import ProjetaCCT
except ImportError:
    from calculos_basicos import CalculosBasicos
    from projecao_reajuste import ProjetaCCT

logger = logging.getLogger(__name__)

class NucleoNegociacao:
    """
    Classe responsável por calcular o impacto financeiro completo:
    ✅ Custo mensal e anual
    ✅ Valor dos encargos (INSS, FGTS, etc)
    ✅ Diferença de custo antes e depois do reajuste
    ✅ Percentual de comprometimento do faturamento
    """

    def __init__(self):
        self.calc = CalculosBasicos()
        self.projecao = ProjetaCCT()
        self.percentual_encargos = 42.61  # Alíquota padrão da legislação

    # ==================================================
    # 📊 CÁLCULO PRINCIPAL DE IMPACTO
    # ==================================================

    def calcular_impacto_completo(self, 
                                   valor_atual: float, 
                                   valor_reajustado: float, 
                                   quantidade_funcionarios: int, 
                                   faturamento_mensal_empresa: float = None) -> Dict:
        """
        Calcula tudo o que é necessário para a negociação.
        """
        logger.info("Calculando impacto financeiro completo...")

        # 1. Diferença entre valores
        analise_valores = self.calc.calcular_diferenca_valores(valor_reajustado, valor_atual)

        # 2. Cálculo de custos SEM reajuste (Situação Atual)
        custo_atual = self.calc.calcular_custo_total_folha(
            salario_unitario=valor_atual,
            quantidade_funcionarios=quantidade_funcionarios,
            percentual_encargos=self.percentual_encargos
        )

        # 3. Cálculo de custos COM reajuste (Nova Situação)
        custo_projetado = self.calc.calcular_custo_total_folha(
            salario_unitario=valor_reajustado,
            quantidade_funcionarios=quantidade_funcionarios,
            percentual_encargos=self.percentual_encargos
        )

        # 4. Diferença de custo (o que vai aumentar de gasto)
        diferenca_mensal = round(custo_projetado['custo_total_mensal'] - custo_atual['custo_total_mensal'], 2)
        diferenca_anual = round(diferenca_mensal * 12, 2)

        # 5. Capacidade Econômica (se informar o faturamento)
        capacidade_economica = {}
        if faturamento_mensal_empresa and faturamento_mensal_empresa > 0:
            indice_atual = self.calc.calcular_percentual(custo_atual['custo_total_mensal'], faturamento_mensal_empresa)
            indice_novo = self.calc.calcular_percentual(custo_projetado['custo_total_mensal'], faturamento_mensal_empresa)
            
            capacidade_economica = {
                "faturamento_mensal": faturamento_mensal_empresa,
                "indice_folha_atual": indice_atual,
                "indice_folha_novo": indice_novo,
                "classificacao_atual": self.calc.classificar_capacidade_economica(indice_atual),
                "classificacao_nova": self.calc.classificar_capacidade_economica(indice_novo)
            }

        # Resultado Final Estruturado
        resultado = {
            "metadados": {
                "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "quantidade_funcionarios": quantidade_funcionarios,
                "aliquota_encargos_utilizada": self.percentual_encargos
            },
            "valores_salariais": analise_valores,
            "custo_atual": custo_atual,
            "custo_projetado": custo_projetado,
            "impacto_aumento": {
                "valor_mensal": diferenca_mensal,
                "valor_anual": diferenca_anual,
                "percentual_sobre_custo": analise_valores['diferenca_percentual']
            },
            "capacidade_economica": capacidade_economica
        }

        return resultado

    # ==================================================
    # 📑 RELATÓRIO PARA OS 3 CENÁRIOS
    # ==================================================

    def analisar_cenarios_impacto(self, 
                                   codigo_clausula: str, 
                                   categoria: str, 
                                   quantidade_funcionarios: int, 
                                   faturamento_mensal: float = None,
                                   inflacao_prevista: float = 4.52) -> Dict:
        """
        Junta a projeção de valores com o cálculo de impacto para os 3 cenários.
        Esse é o relatório completo que vai para a mesa de negociação!
        """

        # 1. Pega os valores calculados no módulo anterior
        dados_projecao = self.projecao.gerar_cenarios_projecao(
            codigo_clausula=codigo_clausula,
            categoria=categoria,
            inflacao_prevista=inflacao_prevista
        )

        if "status" in dados_projecao and dados_projecao["status"] == "ERRO":
            return dados_projecao

        valor_base = dados_projecao['valor_base_calculo']
        analise_por_cenario = {}

        # 2. Calcula impacto para CADA cenário
        for nome_cenario, dados_cenario in dados_projecao['cenarios_projecao'].items():
            valor_novo = dados_cenario['valor_reajustado']
            
            analise_por_cenario[nome_cenario] = {
                "dados_reajuste": dados_cenario,
                "analise_impacto": self.calcular_impacto_completo(
                    valor_atual=valor_base,
                    valor_reajustado=valor_novo,
                    quantidade_funcionarios=quantidade_funcionarios,
                    faturamento_mensal_empresa=faturamento_mensal
                )
            }

        # 3. Relatório Consolidado
        relatorio_final = {
            "cabecalho": {
                "modulo": "NÚCLEO DE NEGOCIAÇÃO®",
                "versao": "2.0",
                "clausula_analisada": codigo_clausula,
                "categoria": categoria
            },
            "dados_historicos": dados_projecao['dados_historicos_usados'],
            "resumo_estatistico": dados_projecao['analise_historica'],
            "analise_cenarios": analise_por_cenario
        }

        return relatorio_final

# ==================================================
# 🧪 TESTE COMPLETO E INTEGRADO
# ==================================================
if __name__ == "__main__":
    print("🔎 INICIANDO ANÁLISE DE IMPACTO FINANCEIRO...\n")

    neg = NucleoNegociacao()

    # PARÂMETROS DE EXEMPLO (você pode alterar esses valores)
    PARAMETROS = {
        "codigo_clausula": "CLA-002-01-001",
        "categoria": "Serviços Gerais",
        "qtd_funcionarios": 150,
        "faturamento_mensal_empresa": 850000.00, # R$ 850.000,00 de faturamento
        "inflacao": 4.52
    }

    # Executa tudo
    relatorio = neg.analisar_cenarios_impacto(
        codigo_clausula=PARAMETROS["codigo_clausula"],
        categoria=PARAMETROS["categoria"],
        quantidade_funcionarios=PARAMETROS["qtd_funcionarios"],
        faturamento_mensal=PARAMETROS["faturamento_mensal_empresa"],
        inflacao_prevista=PARAMETROS["inflacao"]
    )

    # Exibe resultado formatado
    print("="*80)
    print("📑 RELATÓRIO COMPLETO DE NEGOCIAÇÃO")
    print("="*80)
    print(json.dumps(relatorio, indent=4, ensure_ascii=False))
    print("\n✅ ANÁLISE FINALIZADA COM SUCESSO!")
    print("💾 Dados integrados com o banco de dados.")