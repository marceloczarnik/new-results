# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: core/fatores_economicos.py
# 📍 FUNÇÃO: Funcionalidade 2 - INTELIGÊNCIA DE MERCADO®
#     Análise de índices econômicos e influência nos reajustes
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
import requests
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime, timedelta
import json

# Importa nossas bases
from calculos_basicos import CalculosBasicos

logger = logging.getLogger(__name__)

class FatoresEconomicos:
    """
    Classe responsável por:
    1. Buscar dados econômicos atualizados (IBGE, BACEN, FGV)
    2. Definir o PESO de influência de cada fator na negociação
    3. Calcular o AJUSTE FINAL da projeção com base no cenário econômico
    """

    def __init__(self):
        self.calc = CalculosBasicos()
        
        # 📊 MATRIZ DE PESOS: Definido por nós, baseado em estudos trabalhistas
        # Quanto maior o número, MAIS influência esse fator tem no resultado
        self.pesos_globais = {
            "inflacao_ipca": 35,      # 35% de influência (MAIS IMPORTANTE: reposição de perdas)
            "inflacao_inpc": 25,      # 25% de influência (focado no custo de vida do trabalhador)
            "crescimento_pib": 15,    # 15% (se a economia cresce, pode dar aumento real)
            "taxa_desemprego": 10,    # 10% (se tem pouca vaga, trabalhador perde força)
            "taxa_cambio_dolar": 5,   # 5% (impacta custo de insumos/exportação)
            "indicadores_setoriais": 7,# 7% (desempenho específico da categoria)
            "fatores_climaticos": 3   # 3% (chuvas/secas - muito importante para agro, por exemplo)
        }

        # Validação: soma dos pesos deve dar 100%
        soma_pesos = sum(self.pesos_globais.values())
        if soma_pesos != 100:
            logger.warning(f"Ajustando pesos. Soma atual: {soma_pesos}% → ajustado para 100%")
            fator_ajuste = 100 / soma_pesos
            for chave in self.pesos_globais:
                self.pesos_globais[chave] *= fator_ajuste

    # ==================================================

    def buscar_dados_economicos(self, ano_base: int) -> Dict:
        """
        Busca índices econômicos das APIs oficiais.
        Nota: Simulamos aqui os valores para funcionar 100% offline,
        mas já deixamos a estrutura pronta para ligar na API real do IBGE/BACEN.
        """
        logger.info(f"Buscando dados econômicos para o ano base: {ano_base}")

        # 🔄 DADOS SIMULADOS (aqui vamos substituir pelas consultas reais futuramente)
        # Esses valores seriam buscados automaticamente na internet
        dados = {
            "ano_referencia": ano_base,
            "inflacao_ipca": 4.52,       # % acumulado do ano
            "inflacao_inpc": 4.38,       # % acumulado do ano
            "crescimento_pib": 2.10,     # % crescimento do PIB
            "taxa_desemprego": 8.7,      # % taxa de desemprego
            "taxa_cambio_dolar": 5.25,    # R$ por USD
            "indicadores_setoriais": 1.8, # Desempenho da categoria vs média
            "fatores_climaticos": -0.5,   # - = ruim / + = bom
            "poder_compra": -0.8          # Variação do poder aquisitivo
        }

        logger.debug(f"Dados econômicos carregados: {dados}")
        return dados

    # ==================================================

    def calcular_indice_influencia(self, valor_fator: float, tipo: str = "positivo") -> float:
        """
        Transforma o valor bruto do índice em uma pontuação de -10 a +10,
        indicando se esse fator ajuda ou atrapalha a negociação.
        
        Args:
            valor_fator: Valor do índice econômico
            tipo: 'positivo' (quanto maior melhor) ou 'negativo' (quanto menor melhor)
        
        Returns:
            Pontuação de -10 a +10
        """
        try:
            # Normaliza o valor para escala -10 a +10
            if tipo == "positivo":
                # Ex: PIB crescendo 3% → bom (+), crescendo 0% → neutro, caindo → ruim (-)
                nota = max(-10, min(10, valor_fator * 2))
            else:
                # Ex: Desemprego 5% → bom (+), desemprego 15% → ruim (-)
                nota = max(-10, min(10, (10 - valor_fator) / 1.5))

            return round(nota, 2)

        except Exception as e:
            logger.error(f"Erro ao calcular influência: {str(e)}")
            return 0.0

    # ==================================================

    def gerar_matriz_impacto(self, dados_economicos: Dict, categoria_especifica: str = "geral") -> Dict:
        """
        Cria a Matriz de Impacto: cruza o valor do índice com seu peso,
        para definir quanto ele interfere no valor final do reajuste.
        """
        matriz = {
            "dados_brutos": dados_economicos,
            "analise_fatores": [],
            "indice_geral_economia": 0.0
        }

        impacto_total = 0

        # 1. Inflação IPCA (Quanto maior, MAIS tem que aumentar o salário)
        nota_ipca = self.calcular_indice_influencia(dados_economicos['inflacao_ipca'], tipo="positivo")
        impacto_ipca = (nota_ipca * self.pesos_globais['inflacao_ipca']) / 100
        matriz["analise_fatores"].append({
            "fator": "Inflação IPCA",
            "valor": dados_economicos['inflacao_ipca'],
            "peso": self.pesos_globais['inflacao_ipca'],
            "nota_influencia": nota_ipca,
            "impacto_percentual": round(impacto_ipca, 4),
            "sentimento": "POSITIVO" if nota_ipca > 0 else "NEGATIVO",
            "explicacao": "Corresponde à perda do poder de compra."
        })
        impacto_total += impacto_ipca

        # 2. Inflação INPC (Mais voltada para famílias)
        nota_inpc = self.calcular_indice_influencia(dados_economicos['inflacao_inpc'], tipo="positivo")
        impacto_inpc = (nota_inpc * self.pesos_globais['inflacao_inpc']) / 100
        matriz["analise_fatores"].append({
            "fator": "Inflação INPC",
            "valor": dados_economicos['inflacao_inpc'],
            "peso": self.pesos_globais['inflacao_inpc'],
            "nota_influencia": nota_inpc,
            "impacto_percentual": round(impacto_inpc, 4),
            "sentimento": "POSITIVO" if nota_inpc > 0 else "NEGATIVO"
        })
        impacto_total += impacto_inpc

        # 3. Crescimento do PIB (Se cresce, empresa tem lucro para dar aumento real)
        nota_pib = self.calcular_indice_influencia(dados_economicos['crescimento_pib'], tipo="positivo")
        impacto_pib = (nota_pib * self.pesos_globais['crescimento_pib']) / 100
        matriz["analise_fatores"].append({
            "fator": "Crescimento do PIB",
            "valor": dados_economicos['crescimento_pib'],
            "peso": self.pesos_globais['crescimento_pib'],
            "nota_influencia": nota_pib,
            "impacto_percentual": round(impacto_pib, 4),
            "sentimento": "POSITIVO" if nota_pib > 0 else "NEGATIVO"
        })
        impacto_total += impacto_pib

        # 4. Taxa de Desemprego (Quanto MENOR, MELHOR para o trabalhador negociar)
        nota_desemp = self.calcular_indice_influencia(dados_economicos['taxa_desemprego'], tipo="negativo")
        impacto_desemp = (nota_desemp * self.pesos_globais['taxa_desemprego']) / 100
        matriz["analise_fatores"].append({
            "fator": "Taxa de Desemprego",
            "valor": dados_economicos['taxa_desemprego'],
            "peso": self.pesos_globais['taxa_desemprego'],
            "nota_influencia": nota_desemp,
            "impacto_percentual": round(impacto_desemp, 4),
            "sentimento": "POSITIVO" if nota_desemp > 0 else "NEGATIVO"
        })
        impacto_total += impacto_desemp

        # ... (os outros fatores seguem a mesma lógica)

        # Índice Geral: -10% (economia péssima) a +10% (economia excelente)
        matriz["indice_geral_economia"] = round(impacto_total / 10, 4)
        matriz["interpretacao_cenario"] = self._interpretar_cenario(matriz["indice_geral_economia"])

        logger.info(f"Análise econômica concluída. Índice Geral: {matriz['indice_geral_economia']}%")
        return matriz

    # ==================================================

    def _interpretar_cenario(self, indice: float) -> str:
        """
        Traduz o número do índice em texto estratégico para negociação.
        """
        if indice >= 5:
            return "✅ CENÁRIO MUITO FAVORÁVEL: Economia aquecida, indicadores positivos. Possibilidade de ganho REAL acima da inflação."
        elif indice >= 2:
            return "🟢 CENÁRIO FAVORÁVEL: Economia estável. Negociação deve ficar próxima da inflação + pequeno aumento real."
        elif indice >= -2:
            return "🟡 CENÁRIO NEUTRO: Economia equilibrada ou sem direção definida. Foco principal em repor a inflação."
        elif indice >= -5:
            return "🟠 CENÁRIO DESFAVORÁVEL: Pressões econômicas. Risco de não repor 100% da inflação ou congelamento."
        else:
            return "🔴 CENÁRIO MUITO DESFAVORÁVEL: Crise/Recessão. Tendência de defasagem salarial, redução de benefícios ou perdas."

    # ==================================================

    def calcular_ajuste_projecao(self, valor_projetado_historico: float, percentual_reajuste: float, matriz_impacto: Dict) -> Dict:
        """
        FUNÇÃO PRINCIPAL:
        Pega o valor que saiu da Projeta CCT® (que usa só histórico)
        e AJUSTA ele para cima ou para baixo de acordo com a economia atual.
        """
        try:
            indice_economia = matriz_impacto['indice_geral_economia']
            
            # Fórmula: Valor Histórico * (1 + (Influência Econômica / 100))
            fator_ajuste = 1 + (indice_economia / 100)
            valor_ajustado = round(valor_projetado_historico * fator_ajuste, 2)
            percentual_ajustado = round(percentual_reajuste * fator_ajuste, 4)

            # Limita ajuste para não ficar irrealista (± 15% no máximo)
            limite_superior = valor_projetado_historico * 1.15
            limite_inferior = valor_projetado_historico * 0.85
            valor_ajustado = max(limite_inferior, min(valor_ajustado, limite_superior))

            return {
                "valor_original_historico": valor_projetado_historico,
                "valor_final_ajustado": valor_ajustado,
                "percentual_reajuste_original": percentual_reajuste,
                "percentual_reajuste_ajustado": percentual_ajustado,
                "fator_ajuste_aplicado": round(fator_ajuste, 4),
                "indice_economico_utilizado": indice_economia,
                "diferenca_valor": round(valor_ajustado - valor_projetado_historico, 2),
                "estrategia_negociacao": matriz_impacto['interpretacao_cenario']
            }

        except Exception as e:
            logger.error(f"Erro ao ajustar projeção: {str(e)}")
            return {}

# ==================================================
# 🧪 TESTE DO MÓDULO
# ==================================================
if __name__ == "__main__":
    # Instancia o módulo
    me = FatoresEconomicos()

    # 1. Pega dados da economia
    dados_econ = me.buscar_dados_economicos(ano_base=2026)

    # 2. Gera matriz de impacto
    matriz = me.gerar_matriz_impacto(dados_econ, categoria_especifica="Comércio")

    # 3. Simula ajuste em um valor que veio da Projeta CCT®
    resultado_ajuste = me.calcular_ajuste_projecao(
        valor_projetado_historico=2000.00,  # Valor que deu só pelo histórico
        percentual_reajuste=5.50,           # Reajuste histórico
        matriz_impacto=matriz
    )

    # Resultado
    print("="*70)
    print("📊 INTELIGÊNCIA DE MERCADO® - ANÁLISE COMPLETA")
    print("="*70)
    print(json.dumps(matriz, indent=4, ensure_ascii=False))
    print("\n")
    print("🔄 AJUSTE DE PROJEÇÃO")
    print(json.dumps(resultado_ajuste, indent=4, ensure_ascii=False))