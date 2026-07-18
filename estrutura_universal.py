# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: padronizacao/estrutura_universal.py
# 📍 FUNÇÃO: Funcionalidade 4 - PONTE NACIONAL DE NORMAS®
#     Define o MODELO OFICIAL de estrutura de CCT
#     Alinhado com o Mediador/MTE
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from typing import List, Dict, Optional, Union
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

# ==================================================
# 📌 ESTRUTURA BASE: DEFINIDA CONFORME LEGISLAÇÃO E MTE
# ==================================================

class TipoClausula(Enum):
    OBRIGATORIA = "OBRIGATÓRIA"     # Tem que ter, senão a CCT é inválida
    FACULTATIVA = "FACULTATIVA"     # Pode ter ou não
    ECONOMICA = "ECONÔMICA"         # Valores, salários, reajustes
    SOCIAL = "SOCIAL"               # Benefícios, saúde, segurança
    PROCESSUAL = "PROCESSUAL"       # Regras de aplicação, vigência

class EstruturaUniversal:
    """
    Classe que representa o MODELO PADRÃO de qualquer CCT do Brasil.
    Contém todos os Capítulos, Seções e Cláusulas que existem no sistema governamental.
    Qualquer arquivo que entrar no sistema será reorganizado para essa estrutura.
    """

    def __init__(self):
        self.versao_estrutura = "2.0 - ALINHADA COM MTE 2026"
        self.data_atualizacao = "08/06/2026"
        
        # 📚 ESTRUTURA COMPLETA DE CAPÍTULOS E CLÁUSULAS
        # Baseado no que é aceito no Mediador e no Sistema de Registro de Normas
        self.estrutura_completa = [
            {
                "codigo": "CAP-001",
                "titulo": "DISPOSIÇÕES GERAIS",
                "descricao": "Define as partes, abrangência, categoria profissional e vigência",
                "secoes": [
                    {
                        "codigo": "SEC-001-01",
                        "titulo": "Identificação das Partes",
                        "clausulas": [
                            {"codigo": "CLA-001-01-001", "nome": "Sindicato Profissional", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Qualificação completa da entidade representante dos trabalhadores"},
                            {"codigo": "CLA-001-01-002", "nome": "Sindicato Patronal / Empresas", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Qualificação completa da entidade ou empresas acordantes"},
                            {"codigo": "CLA-001-01-003", "nome": "Representação Legal", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Nome e cargo dos negociadores e signatários"}
                        ]
                    },
                    {
                        "codigo": "SEC-001-02",
                        "titulo": "Abrangência e Vigência",
                        "clausulas": [
                            {"codigo": "CLA-001-02-001", "nome": "Âmbito Territorial", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Cidades e estados onde a CCT vale"},
                            {"codigo": "CLA-001-02-002", "nome": "Âmbito Profissional / Categoria", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Quais cargos/funções são cobertos"},
                            {"codigo": "CLA-001-02-003", "nome": "Prazo de Vigência", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Data de início e fim da norma (geralmente 2 anos)"}
                        ]
                    }
                ]
            },
            {
                "codigo": "CAP-002",
                "titulo": "RELAÇÕES SALARIAIS",
                "descricao": "Tudo que envolve dinheiro, pagamento, reajustes e pisos",
                "secoes": [
                    {
                        "codigo": "SEC-002-01",
                        "titulo": "Salários e Reajustes",
                        "clausulas": [
                            {"codigo": "CLA-002-01-001", "nome": "Piso Salarial Normativo", "tipo": TipoClausula.ECONOMICA.value, "descricao": "Valor mínimo da categoria, por função ou geral"},
                            {"codigo": "CLA-002-01-002", "nome": "Reajuste Salarial", "tipo": TipoClausula.ECONOMICA.value, "descricao": "Percentual e data do aumento salarial"},
                            {"codigo": "CLA-002-01-003", "nome": "Cálculo e Pagamento de Salários", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Forma, local e data de pagamento"},
                            {"codigo": "CLA-002-01-004", "nome": "Adicionais Salariais", "tipo": TipoClausula.FACULTATIVA.value, "descricao": "Periculosidade, insalubridade, noturno, etc."}
                        ]
                    }
                ]
            },
            {
                "codigo": "CAP-003",
                "titulo": "BENEFÍCIOS SOCIAIS",
                "descricao": "Auxílios, vale-refeição, transporte, saúde, educação",
                "secoes": [
                    {
                        "codigo": "SEC-003-01",
                        "titulo": "Auxílios e Ajuda de Custo",
                        "clausulas": [
                            {"codigo": "CLA-003-01-001", "nome": "Vale-Alimentação / Refeição", "tipo": TipoClausula.SOCIAL.value, "descricao": "Valor, forma e regras de concessão"},
                            {"codigo": "CLA-003-01-002", "nome": "Auxílio Transporte", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Conforme lei e acréscimos da CCT"},
                            {"codigo": "CLA-003-01-003", "nome": "Auxílio Creche / Filhos", "tipo": TipoClausula.SOCIAL.value, "descricao": "Valores e limites de idade"},
                            {"codigo": "CLA-003-01-004", "nome": "Assistência Médica / Odontológica", "tipo": TipoClausula.SOCIAL.value, "descricao": "Cobertura e regras"}
                        ]
                    }
                ]
            },
            {
                "codigo": "CAP-004",
                "titulo": "CONDIÇÕES DE TRABALHO",
                "descricao": "Jornada, horário, férias, segurança, saúde",
                "secoes": [
                    {
                        "codigo": "SEC-004-01",
                        "titulo": "Jornada e Horário",
                        "clausulas": [
                            {"codigo": "CLA-004-01-001", "nome": "Jornada de Trabalho", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Carga horária semanal e diária"},
                            {"codigo": "CLA-004-01-002", "nome": "Horas Extras", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Percentuais de acréscimo e limites"},
                            {"codigo": "CLA-004-01-003", "nome": "Intervalos e Descansos", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Convenções legais e acordadas"}
                        ]
                    }
                ]
            },
            {
                "codigo": "CAP-005",
                "titulo": "CUMPRIMENTO E DISPOSIÇÕES FINAIS",
                "descricao": "Multas, fiscalização, divergências, prorrogação",
                "secoes": [
                    {
                        "codigo": "SEC-005-01",
                        "titulo": "Regras Gerais",
                        "clausulas": [
                            {"codigo": "CLA-005-01-001", "nome": "Cumprimento da Convenção", "tipo": TipoClausula.OBRIGATORIA.value, "descricao": "Obrigação de aplicar o combinado"},
                            {"codigo": "CLA-005-01-002", "nome": "Multas por Descumprimento", "tipo": TipoClausula.PROCESSUAL.value, "descricao": "Valor e destino das multas"},
                            {"codigo": "CLA-005-01-003", "nome": "Solução de Conflitos", "tipo": TipoClausula.PROCESSUAL.value, "descricao": "Mediação, arbitragem ou justiça do trabalho"}
                        ]
                    }
                ]
            }
        ]

    # ==================================================

    def listar_todos_elementos(self) -> Dict:
        """
        Retorna a estrutura completa em formato dicionário, pronta para usar.
        """
        return {
            "metadados": {
                "versao": self.versao_estrutura,
                "atualizado_em": self.data_atualizacao,
                "total_capitulos": len(self.estrutura_completa)
            },
            "estrutura": self.estrutura_completa
        }

    # ==================================================

    def buscar_clausula_por_codigo(self, codigo: str) -> Optional[Dict]:
        """
        Procura uma cláusula específica pelo seu código único.
        """
        for capitulo in self.estrutura_completa:
            for secao in capitulo['secoes']:
                for clausula in secao['clausulas']:
                    if clausula['codigo'] == codigo:
                        # Retorna com o caminho completo
                        return {
                            "codigo": codigo,
                            "nome": clausula['nome'],
                            "tipo": clausula['tipo'],
                            "descricao": clausula['descricao'],
                            "capitulo_codigo": capitulo['codigo'],
                            "capitulo_nome": capitulo['titulo'],
                            "secao_codigo": secao['codigo'],
                            "secao_nome": secao['titulo']
                        }
        logger.warning(f"Cláusula com código {codigo} não encontrada na estrutura padrão.")
        return None

    # ==================================================

    def listar_clausulas_obrigatorias(self) -> List[Dict]:
        """
        Retorna apenas as cláusulas que SÃO OBRIGATÓRIAS por lei.
        Usado na validação para ver se a CCT está completa.
        """
        obrigatorias = []
        for capitulo in self.estrutura_completa:
            for secao in capitulo['secoes']:
                for clausula in secao['clausulas']:
                    if clausula['tipo'] == TipoClausula.OBRIGATORIA.value:
                        obrigatorias.append({
                            **clausula,
                            "capitulo": capitulo['titulo'],
                            "secao": secao['titulo']
                        })
        return obrigatorias

    # ==================================================

    def exportar_json(self, caminho_saida: str = "estrutura_padrao_cct.json") -> bool:
        """
        Salva a estrutura completa em um arquivo JSON para consulta externa.
        """
        try:
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                json.dump(self.listar_todos_elementos(), f, indent=4, ensure_ascii=False)
            logger.info(f"Estrutura padrão exportada para: {caminho_saida}")
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar estrutura: {str(e)}")
            return False

# ==================================================
# 🧪 TESTE DA ESTRUTURA
# ==================================================
if __name__ == "__main__":
    # Cria o modelo padrão
    modelo = EstruturaUniversal()

    # 1. Lista quantos capítulos temos
    dados = modelo.listar_todos_elementos()
    print(f"📚 ESTRUTURA PADRÃO DE CCT - VERSÃO: {dados['metadados']['versao']}")
    print(f"📑 Total de Capítulos Definidos: {dados['metadados']['total_capitulos']}\n")

    # 2. Exibe todas as cláusulas OBRIGATÓRIAS
    print("⚠️ CLÁUSULAS OBRIGATÓRIAS POR LEI:")
    obrigatorias = modelo.listar_clausulas_obrigatorias()
    for cla in obrigatorias:
        print(f" - {cla['codigo']}: {cla['nome']}")

    # 3. Busca uma cláusula específica
    print("\n🔍 BUSCA DE CLÁUSULA ESPECÍFICA (Piso Salarial):")
    resultado = modelo.buscar_clausula_por_codigo("CLA-002-01-001")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))

    # 4. Exporta o modelo para arquivo
    modelo.exportar_json()
    print("\n💾 Arquivo 'estrutura_padrao_cct.json' gerado com sucesso!")