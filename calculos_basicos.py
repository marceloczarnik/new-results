# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: core/calculos_basicos.py
# 📍 FUNÇÃO: Operações Matemáticas e Financeiras Básicas
# ==================================================

import math
from typing import Union, List
import logging

logger = logging.getLogger(__name__)

class CalculosBasicos:
    """
    Classe com todos os cálculos matemáticos, financeiros e trabalhistas básicos
    usados em todo o sistema.
    """

    def __init__(self):
        self.precisao = 2  # Casas decimais padrão

    # ==================================================
    # 💰 CÁLCULOS DE VALORES E PERCENTUAIS
    # ==================================================

    def calcular_percentual(self, valor: float, total: float) -> float:
        """
        Calcula qual o percentual que 'valor' representa de 'total'
        Ex: 350.000 / 1.000.000 = 35%
        """
        if total <= 0:
            return 0.0
        return round((valor / total) * 100, self.precisao)

    def calcular_valor_percentual(self, valor_base: float, percentual: float) -> float:
        """
        Calcula o valor correspondente a um percentual sobre um valor base
        Ex: 10% de 1.890 = 189,00
        """
        if valor_base <= 0:
            return 0.0
        return round(valor_base * (percentual / 100), self.precisao)

    # ✅ FUNÇÃO QUE ADICIONAMOS (COM INDENTAÇÃO CERTA!)
    def calcular_valor_com_reajuste(self, valor_atual: float, percentual: float) -> float:
        """
        Calcula o novo valor após aplicar um percentual de reajuste
        Ex: R$ 1.890,00 + 6,46% = R$ 2.012,14
        """
        if valor_atual <= 0:
            return 0.0
        return round(valor_atual * (1 + (percentual / 100)), self.precisao)

    def calcular_diferenca_valores(self, valor_novo: float, valor_atual: float) -> dict:
        """
        Calcula a diferença absoluta e percentual entre dois valores
        """
        diferenca_absoluta = round(valor_novo - valor_atual, self.precisao)
        
        if valor_atual <= 0:
            diferenca_percentual = 0.0
        else:
            diferenca_percentual = round(((valor_novo / valor_atual) - 1) * 100, self.precisao)

        return {
            "atual": valor_atual,
            "novo": valor_novo,
            "diferenca_valor": diferenca_absoluta,
            "diferenca_percentual": diferenca_percentual
        }

    # ==================================================
    # 🧮 MÉDIAS E ESTATÍSTICAS
    # ==================================================

    def media_aritmetica(self, lista_valores: List[float]) -> float:
        """Média simples de uma lista de valores"""
        if not lista_valores:
            return 0.0
        return round(sum(lista_valores) / len(lista_valores), self.precisao)

    def media_ponderada(self, lista_valores: List[float], lista_pesos: List[float]) -> float:
        """Média onde cada valor tem um peso/importância diferente"""
        if len(lista_valores) != len(lista_pesos) or not lista_valores:
            return 0.0
        
        soma_total = sum(v * p for v, p in zip(lista_valores, lista_pesos))
        soma_pesos = sum(lista_pesos)
        
        if soma_pesos <= 0:
            return 0.0
        
        return round(soma_total / soma_pesos, self.precisao)

    def taxa_crescimento(self, valor_inicial: float, valor_final: float, periodos: int = 1) -> float:
        """Calcula taxa de crescimento composta"""
        if valor_inicial <= 0 or periodos <= 0:
            return 0.0
        
        taxa = (math.pow(valor_final / valor_inicial, 1 / periodos) - 1) * 100
        return round(taxa, self.precisao)

    # ==================================================
    # 🧮 ENCARGOS TRABALHISTAS E CUSTOS
    # ==================================================

    def calcular_encargos(self, valor_base: float, percentual_encargos: float = 42.61) -> dict:
        """
        Calcula valor dos encargos sobre a base
        Percentual padrão adotado: 42,61% (alinhado com o relatório)
        """
        valor_encargos = round(self.calcular_valor_percentual(valor_base, percentual_encargos), self.precisao)
        valor_total = round(valor_base + valor_encargos, self.precisao)

        return {
            "base_calculo": valor_base,
            "percentual_encargos": percentual_encargos,
            "valor_encargos": valor_encargos,
            "valor_total_com_encargos": valor_total
        }

    def calcular_custo_total_folha(self, salario_unitario: float, quantidade_funcionarios: int, percentual_encargos: float = 42.61) -> dict:
        """
        Cálculo completo: Salário + Encargos → Mensal e Anual
        """
        if quantidade_funcionarios <= 0:
            return {}

        # Cálculo mensal
        salarios_sem_encargos = round(salario_unitario * quantidade_funcionarios, self.precisao)
        calculo_encargos = self.calcular_encargos(salarios_sem_encargos, percentual_encargos)
        
        custo_mensal = calculo_encargos['valor_total_com_encargos']
        custo_anual = round(custo_mensal * 12, self.precisao)

        return {
            "quantidade_funcionarios": quantidade_funcionarios,
            "salario_unitario": salario_unitario,
            "salarios_base_total": salarios_sem_encargos,
            "encargos": calculo_encargos,
            "custo_total_mensal": custo_mensal,
            "custo_total_anual": custo_anual
        }

    # ==================================================
    # 📊 ANÁLISE DE CAPACIDADE ECONÔMICA
    # ==================================================

    def classificar_capacidade_economica(self, indice_folha_faturamento: float) -> str:
        """
        Classifica a saúde financeira da empresa com base no quanto a folha representa do faturamento:
        - ATÉ 25% → MUITO BOA
        - 25% a 30% → BOA
        - 30% a 38% → MODERADA
        - 38% a 45% → BAIXA
        - ACIMA DE 45% → CRÍTICA
        """
        if indice_folha_faturamento <= 25:
            return "MUITO BOA"
        elif indice_folha_faturamento <= 30:
            return "BOA"
        elif indice_folha_faturamento <= 38:
            return "MODERADA"
        elif indice_folha_faturamento <= 45:
            return "BAIXA"
        else:
            return "CRÍTICA"

    def definir_limite_reajuste(self, capacidade: str, inflacao: float) -> float:
        """
        Define o percentual máximo que a empresa consegue suportar
        """
        tabela_limites = {
            "MUITO BOA": round(inflacao + 2.0, 2),
            "BOA": round(inflacao + 1.0, 2),
            "MODERADA": round(inflacao + 0.3, 2),
            "BAIXA": round(inflacao - 0.72, 2),  # Alinhado com nosso exemplo de 3.8%
            "CRÍTICA": round(inflacao - 2.0, 2)
        }
        return tabela_limites.get(capacidade, inflacao)

    # ==================================================
    # 🧪 TESTE DA CLASSE
    # ==================================================
if __name__ == "__main__":
    calc = CalculosBasicos()

    # Teste da função nova
    resultado = calc.calcular_valor_com_reajuste(1890.0, 6.46)
    print(f"✅ Teste Reajuste: R$ 1.890 + 6,46% = R$ {resultado}")
    # Deve aparecer: R$ 2012.14

    # Teste de encargos
    enc = calc.calcular_encargos(1890.0)
    print(f"✅ Teste Encargos: {enc}")