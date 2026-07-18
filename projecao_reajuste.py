# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: core/projecao_reajuste.py
# 📍 FUNÇÃO: Projeção de Valores e Reajustes
#     Funcionalidade 2 - PROJETA CCT®
#     AGORA CONECTADO AO BANCO DE DADOS! 💾
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime
import json

# Importa os cálculos básicos
try:
    from .calculos_basicos import CalculosBasicos
except ImportError:
    from calculos_basicos import CalculosBasicos

# ✅ NOVO: Importa o Banco de Dados
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Volta uma pasta
from dados.banco_sindical import BancoSindical

logger = logging.getLogger(__name__)

class ProjetaCCT:
    """
    Classe responsável por projetar valores futuros com base em:
    - Histórico de valores (AGORA VEM DO BANCO DE DADOS 💾)
    - Inflação projetada
    - Perfil de crescimento
    """

    def __init__(self):
        self.calc = CalculosBasicos()
        self.db = BancoSindical() # ✅ Conecta automaticamente ao banco
        self.pesos_historicos = {
            'ano_1': 0.40,  # Último ano → maior peso
            'ano_2': 0.30,
            'ano_3': 0.15,
            'ano_4': 0.10,
            'ano_5': 0.05   # Ano mais antigo → menor peso
        }

    # ==================================================
    # 📌 MÉTODO ATUALIZADO: PEGA DADOS DIRETO DO BANCO
    # ==================================================

    def carregar_historico_valores(self, codigo_clausula: str, categoria: str = None) -> List[Dict]:
        """
        Busca todo o histórico de valores de uma cláusula específica
        diretamente do Banco de Dados.
        Ex: codigo_clausula = "CLA-002-01-001" (Piso Salarial)
        """
        logger.info(f"Buscando histórico no banco para: {codigo_clausula} | Categoria: {categoria}")
        
        # ✅ Aqui é onde buscamos os dados salvos
        dados_historicos = self.db.buscar_historico_por_clausula(codigo_clausula, categoria)

        if not dados_historicos:
            logger.warning("⚠️ Nenhum dado encontrado no banco. Usando valores de exemplo para simulação.")
            # Dados de exemplo completos para simular cálculo real
            return [
                {"ano": 2021, "valor": 1500.00, "variacao_percentual": 4.5},
                {"ano": 2022, "valor": 1580.00, "variacao_percentual": 5.33},
                {"ano": 2023, "valor": 1670.00, "variacao_percentual": 5.70},
                {"ano": 2024, "valor": 1780.00, "variacao_percentual": 6.58},
                {"ano": 2025, "valor": 1890.00, "variacao_percentual": 6.18}
            ]
        
        # Ordena por ano (garante a ordem correta)
        return sorted(dados_historicos, key=lambda x: x['ano'])

    # ==================================================

    def calcular_variacao_media(self, dados_historicos: List[Dict]) -> Dict:
        """
        Calcula a média de reajuste dos últimos anos,
        usando média aritmética e média ponderada.
        """
        if len(dados_historicos) < 2:
            return {"erro": "Dados insuficientes para cálculo"}

        # Pega apenas as variações dos últimos 5 anos
        variacoes = [item['variacao_percentual'] for item in dados_historicos[-5:]]
        
        media_aritmetica = round(sum(variacoes) / len(variacoes), 2)
        
        # Média ponderada (dá mais peso aos anos mais recentes)
        pesos = list(self.pesos_historicos.values())[:len(variacoes)]
        media_ponderada = round(np.dot(variacoes, pesos), 2)

        return {
            "media_aritmetica": media_aritmetica,
            "media_ponderada": media_ponderada,
            "ultima_variacao": round(variacoes[-1], 2),
            "maior_variacao": round(max(variacoes), 2),
            "menor_variacao": round(min(variacoes), 2)
        }

    # ==================================================

    def projetar_por_indice(self, valor_atual: float, indice: float, inflacao_prevista: float = None) -> Dict:
        """
        Projeta o valor futuro aplicando um percentual de reajuste.
        """
        valor_reajustado = self.calc.calcular_valor_com_reajuste(valor_atual, indice)
        
        # Cálculo de ganho/perda real
        if inflacao_prevista and inflacao_prevista > 0:
            ganho_real = round(indice - inflacao_prevista, 2)
            poder_compra = round(valor_reajustado / (1 + (inflacao_prevista/100)) - valor_atual, 2)
        else:
            ganho_real = 0.0
            poder_compra = 0.0

        return {
            "valor_atual": round(valor_atual, 2),
            "percentual_reajuste": round(indice, 2),
            "valor_reajustado": round(valor_reajustado, 2),
            "ganho_perda_real": ganho_real,
            "variacao_poder_compra": poder_compra
        }

    # ==================================================

    def gerar_cenarios_projecao(self, codigo_clausula: str, categoria: str = None, inflacao_prevista: float = 4.5) -> Dict:
        """
        Método PRINCIPAL: Junta tudo.
        1. Busca dados do Banco 💾
        2. Calcula médias
        3. Gera 3 cenários: Pessimista, Moderado e Otimista
        """
        # 1. Pega dados do banco ou exemplo
        historico = self.carregar_historico_valores(codigo_clausula, categoria)
        
        if not historico:
            return {"status": "ERRO", "mensagem": "Não foi possível obter histórico"}

        # 2. Calcula estatísticas do histórico
        analise_historica = self.calcular_variacao_media(historico)
        if "erro" in analise_historica:
            return {"status": "ERRO", "mensagem": analise_historica['erro']}

        valor_atual = historico[-1]['valor'] # Valor do último ano cadastrado

        # 3. Define os cenários com base nos dados
        cenarios = {
            "📉 CENÁRIO PESSIMISTA (apenas reposição inflação)": 
                self.projetar_por_indice(valor_atual, inflacao_prevista, inflacao_prevista),
            
            "⚖️ CENÁRIO MODERADO (média dos últimos anos)": 
                self.projetar_por_indice(valor_atual, analise_historica['media_ponderada'], inflacao_prevista),
            
            "📈 CENÁRIO OTIMISTA (igual último reajuste)": 
                self.projetar_por_indice(valor_atual, analise_historica['ultima_variacao'], inflacao_prevista)
        }

        resultado_final = {
            "metadados": {
                "clausula": codigo_clausula,
                "categoria": categoria,
                "ano_referencia": datetime.now().year,
                "inflacao_prevista": inflacao_prevista
            },
            "dados_historicos_usados": historico,
            "analise_historica": analise_historica,
            "cenarios_projecao": cenarios,
            "valor_base_calculo": valor_atual
        }

        # ✅ Salva essa projeção no banco também!
        self.db.salvar_projecao(
            dados_projecao={"codigo_clausula": codigo_clausula, "categoria": categoria},
            resultado=resultado_final
        )

        return resultado_final

# ==================================================
# 🧪 TESTE AGORA CONECTADO AO BANCO!
# ==================================================
if __name__ == "__main__":
    print("🔄 INICIANDO PROJEÇÃO CCT® - CONECTADO AO BANCO DE DADOS 💾\n")

    proj = ProjetaCCT()

    # Código da cláusula que queremos projetar (Piso Salarial)
    CODIGO_ALVO = "CLA-002-01-001"
    CATEGORIA_ALVO = "Serviços Gerais"

    # Executa tudo
    resultado = proj.gerar_cenarios_projecao(
        codigo_clausula=CODIGO_ALVO,
        categoria=CATEGORIA_ALVO,
        inflacao_prevista=4.52 # Inflação que usamos no relatório anterior
    )

    # Exibe resultado formatado
    print("="*80)
    print("📊 RELATÓRIO DE PROJEÇÃO - PROJETA CCT®")
    print("="*80)
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
    print("\n✅ PROCESSO FINALIZADO! Dados lidos e salvos no banco.")