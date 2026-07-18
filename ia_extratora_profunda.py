import json
from pydantic import BaseModel, Field
from typing import List, Optional

# 1. Definimos a estrutura exata que queremos que a IA nos devolva.
# Como pós-doutores, sabemos que não basta o "salário", precisamos das condicionantes!
class PisoSalarialCargo(BaseModel):
    cargo_cct: str = Field(description="Nome do cargo conforme escrito na Convenção Coletiva.")
    cbo_relacionada: Optional[str] = Field(description="CBO explicitamente mencionada na CCT ou inferida tecnicamente.")
    valor_piso: float = Field(description="O valor nominal do piso salarial (transformar 'R$ 2.500,00' em 2500.00).")
    jornada_vinculada: str = Field(description="Jornada para este piso (ex: 220h, 180h, 6h diárias, 12x36).")
    vigencia_piso: str = Field(description="Período de vigência específico deste valor (ex: 2025-2026).")
    condicional_aplicacao: Optional[str] = Field(description="Caso haja alguma condição para pagar esse valor (ex: 'Apenas para empresas sem plano de saúde', 'Após o período de experiência').")

class ClausulaSateliteRelevante(BaseModel):
    titulo_clausula: str = Field(description="Título ou número da cláusula (ex: 'CLÁUSULA QUARTA - VALE REFEIÇÃO').")
    resumo_tecnico: str = Field(description="Resumo jurídico-operacional do direito (ex: 'Vale refeição obrigatório de R$ 35,00 por dia trabalhado').")
    impacto_financeiro_direto: bool = Field(description="Indica se essa cláusula gera custo direto na folha de pagamento além do salário.")

class DiagnosticoCCTSatelite(BaseModel):
    sindicato_profissional: str = Field(description="Nome completo do Sindicato dos Empregados.")
    sindicato_patronal: str = Field(description="Nome completo do Sindicato das Empresas (Patronal).")
    pisos_salariais_identificados: List[PisoSalarialCargo]
    clausulas_criticas_encontradas: List[ClausulaSateliteRelevante]


class IAExtratoraProfunda:
    def __init__(self):
        pass

    def gerar_prompt_hermeneutico(self, texto_bruto_pdf: str, categoria_alvo: str) -> str:
        """
        Gera o prompt mestre com rigor de Pós-Doutor para orientar a LLM (IA).
        """
        prompt = f"""
        Você é um LLM especializado em Direito Coletivo do Trabalho e atua como um Auditor de Compliance Sindical sênior.
        Sua missão é ler o texto bruto de uma Convenção Coletiva de Trabalho (CCT) e extrair os dados com precisão cirúrgica para a categoria: "{categoria_alvo}".

        --- TEXTO BRUTO DO PDF DA CCT ---
        {texto_bruto_pdf}
        ---------------------------------

        DIRETRIZES TÉCNICAS DE EXTRAÇÃO:
        1. Ignore cláusulas genéricas, focando estritamente no que afeta a categoria indicada ("{categoria_alvo}").
        2. Localize a tabela de Pisos Salariais. Converta todos os valores monetários para floats puros (Ex: R$ 3.120,50 vira 3120.50).
        3. Identifique as nuances da jornada (Ex: se para Telemarketing constar 180h ou 36h semanais, registre exatamente).
        4. Verifique cláusulas de impacto financeiro satélite (Auxílio-Creche, Vale Alimentação diferenciado, Quebra de Caixa, Adicionais de Periculosidade/Insalubridade fixados em Convenção).
        5. Se houver dubiedade ou regras de transição (ex: um salário até maio, outro após junho), utilize o campo 'condicional_aplicacao' para explicar a regra de cálculo.

        A sua resposta deve seguir estritamente o formato JSON e respeitar os tipos de dados definidos pelo esquema da aplicação. Não adicione textos explicativos fora do JSON.
        """
        return prompt

    def simular_resposta_ia(self):
        """
        Simula a estrutura do JSON perfeito que a IA devolverá ao rodar o prompt acima 
        sobre um PDF de CCT de Motoristas.
        """
        exemplo_retorno_ia = {
            "sindicato_profissional": "SINDICATO DOS TRABALHADORES EM TRANSPORTES RODOVIARIOS DE CARGA E PASSAGEIROS",
            "sindicato_patronal": "SINDICATO DAS EMPRESAS DE TRANSPORTES DE CARGA (SINDILOG)",
            "pisos_salariais_identificados": [
                {
                    "cargo_cct": "Motorista de Caminhão Truque / Carreta",
                    "cbo_relacionada": "7825-10",
                    "valor_piso": 3450.00,
                    "jornada_vinculada": "220h mensais (Lei 13.103)",
                    "vigencia_piso": "01/05/2025 a 30/04/2026",
                    "condicional_aplicacao": "Valor base. Não inclui o tempo de espera que deve ser pago com adicional de 30% da hora normal."
                },
                {
                    "cargo_cct": "Ajudante de Motorista / Movimentador",
                    "cbo_relacionada": "7832-25",
                    "valor_piso": 1820.00,
                    "jornada_vinculada": "220h mensais",
                    "vigencia_piso": "01/05/2025 a 30/04/2026",
                    "condicional_aplicacao": "Nenhuma"
                }
            ],
            "clausulas_criticas_encontradas": [
                {
                    "titulo_clausula": "CLÁUSULA DÉCIMA SEGUNDA - DIÁRIA DE VIAGEM",
                    "resumo_tecnico": "Pagamento obrigatório de R$ 75,00 por dia em viagens que exijam pernoite para custeio de almoço, jantar e pernoite.",
                    "impacto_financeiro_direto": True
                },
                {
                    "titulo_clausula": "CLÁUSULA VIGÉSIMA - SEGURO DE VIDA",
                    "resumo_tecnico": "Apólice de seguro de vida obrigatória custeada integralmente pela empresa com cobertura mínima de 10 vezes o piso salarial para morte natural ou acidental.",
                    "impacto_financeiro_direto": True
                }
            ]
        }
        return exemplo_retorno_ia

if __name__ == "__main__":
    extrator = IAExtratoraProfunda()
    # Exemplo visual do output que será injetado no banco de dados do seu site
    print("=== MODELO DE DADOS QUE A IA VAI GRAVAR NO BANCO (JSON ESTRUTURADO) ===")
    print(json.dumps(extrator.simular_resposta_ia(), indent=2, ensure_ascii=False))