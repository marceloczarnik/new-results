# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: padronizacao/validador_normas.py
# 📍 FUNÇÃO: Validação, Verificação e Conformidade Legal
#     Funcionalidade 4 - PONTE NACIONAL DE NORMAS®
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import json
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime

# Importa os módulos que já criamos
from estrutura_universal import EstruturaUniversal, TipoClausula
from conversor_texto import ConversorTexto

logger = logging.getLogger(__name__)

class ValidadorNormas:
    """
    Classe responsável por:
    1. Verificar se TODAS as cláusulas obrigatórias estão presentes
    2. Checar consistência de datas, valores e informações legais
    3. Apontar erros, omissões e irregularidades
    4. Gerar o Certificado de Conformidade para envio ao Governo
    """

    def __init__(self):
        self.estrutura_padrao = EstruturaUniversal()
        self.conversor = ConversorTexto()
        
        # Carrega a lista oficial do que é obrigatório
        self.lista_obrigatorias = self.estrutura_padrao.listar_clausulas_obrigatorias()
        self.codigos_obrigatorios = [clausula['codigo'] for clausula in self.lista_obrigatorias]

    # ==================================================

    def verificar_completude(self, dados_mapeados: Dict) -> Dict:
        """
        🕵️ VERIFICAÇÃO PRINCIPAL:
        Compara o que foi encontrado no arquivo com o que DEVERIA ter (por lei).
        """
        resultado = {
            "status_validacao": "PENDENTE",
            "resumo": {
                "total_obrigatorias": len(self.codigos_obrigatorios),
                "encontradas": 0,
                "faltantes": 0,
                "facultativas_encontradas": 0
            },
            "lista_faltantes": [],
            "lista_encontradas": [],
            "avisos": [],
            "erros": []
        }

        # Pega todas as cláusulas que o conversor conseguiu mapear com código oficial
        clausulas_arquivo = dados_mapeados.get("conteudo_identificado", {}).get("clausulas", [])
        codigos_encontrados = []

        for cla in clausulas_arquivo:
            cod = cla.get("codigo_estrutura")
            if cod:
                codigos_encontrados.append(cod)
                resultado["lista_encontradas"].append({
                    "codigo": cod,
                    "titulo_original": cla.get("titulo"),
                    "titulo_oficial": self.estrutura_padrao.buscar_clausula_por_codigo(cod).get("nome", "N/A"), # pyright: ignore[reportOptionalMemberAccess]
                    "status": "OK"
                })
            else:
                # Cláusula existe no texto mas não foi reconhecida no padrão
                resultado["avisos"].append({
                    "tipo": "MAPEAMENTO",
                    "mensagem": f"Cláusula '{cla.get('titulo')}' não identificada na estrutura oficial. Verificar se é cláusula nova ou erro de digitação."
                })

        # Verifica quais OBRIGATÓRIAS estão FALTANDO
        for cod_obr in self.codigos_obrigatorios:
            if cod_obr in codigos_encontrados:
                resultado["resumo"]["encontradas"] += 1
            else:
                dados_cla = self.estrutura_padrao.buscar_clausula_por_codigo(cod_obr)
                resultado["lista_faltantes"].append({
                    "codigo": cod_obr,
                    "nome": dados_cla.get("nome"), # pyright: ignore[reportOptionalMemberAccess]
                    "capitulo": dados_cla.get("capitulo_nome"), # pyright: ignore[reportOptionalMemberAccess]
                    "gravidade": "🔴 OBRIGATÓRIA",
                    "mensagem": "Esta cláusula é exigida por lei. Sem ela, a CCT não tem validade legal."
                })
                resultado["resumo"]["faltantes"] += 1

        # Conta as facultativas que foram adicionadas
        todas_encontradas = set(codigos_encontrados)
        obrigatorias_set = set(self.codigos_obrigatorios)
        resultado["resumo"]["facultativas_encontradas"] = len(todas_encontradas - obrigatorias_set)

        # Define status geral
        if resultado["resumo"]["faltantes"] == 0:
            resultado["status_validacao"] = "✅ APROVADA"
        elif resultado["resumo"]["faltantes"] <= 2:
            resultado["status_validacao"] = "⚠️ APROVADA COM RESSALVAS"
        else:
            resultado["status_validacao"] = "❌ REPROVADA - FALTAM ITENS OBRIGATÓRIOS"

        logger.info(f"Verificação de completude finalizada. Status: {resultado['status_validacao']}")
        return resultado

    # ==================================================

    def verificar_consistencia_dados(self, dados_mapeados: Dict) -> List[Dict]:
        """
        📊 Verifica se os dados fazem sentido:
        - Data de vigência: fim não pode ser antes do início
        - Pisos e valores: não podem ser zero ou negativos
        - CNPJs e dados cadastrais: formato básico
        """
        alertas = []
        texto_completo = str(dados_mapeados)

        # 1. Verificação de Datas
        if "vigência" in texto_completo.lower() or "validade" in texto_completo.lower():
            # Lógica simples de exemplo - vamos aprofundar depois
            if "2024" in texto_completo and "2025" not in texto_completo and "2026" not in texto_completo:
                alertas.append({
                    "tipo": "DATA",
                    "gravidade": "⚠️ ATENÇÃO",
                    "mensagem": "A vigência parece ser apenas para ano passado. Verificar se não está desatualizada."
                })

        # 2. Verificação de Valores
        if "piso salarial" in texto_completo.lower():
            if "r$ 0,00" in texto_completo or "r$ 0,0" in texto_completo:
                alertas.append({
                    "tipo": "VALOR",
                    "gravidade": "❌ ERRO",
                    "mensagem": "Piso salarial encontrado com valor R$ 0,00. Isso é inválido."
                })
            if "r$ 1," in texto_completo or "r$ 2," in texto_completo:
                alertas.append({
                    "tipo": "VALOR",
                    "gravidade": "⚠️ SUSPEITA",
                    "mensagem": "Valor de piso muito baixo encontrado. Verificar se não houve erro de digitação (ex: R$ 1.890,00 escrito como R$ 1,890)."
                })

        # 3. Verificação de CNPJ (formato básico)
        import re
        cnpjs_encontrados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto_completo)
        if len(cnpjs_encontrados) < 2:
            alertas.append({
                "tipo": "CADASTRO",
                "gravidade": "⚠️ INCOMPLETO",
                "mensagem": f"Foram encontrados apenas {len(cnpjs_encontrados)} CNPJs. É necessário o CNPJ do Sindicato Profissional e do Patronal."
            })

        return alertas

    # ==================================================

    def gerar_certificado_conformidade(self, resultado_validacao: Dict, caminho_saida: str = None) -> Dict: # pyright: ignore[reportArgumentType]
        """
        📜 Gera o relatório final que garante que a CCT está pronta para o Governo.
        """
        certificado = {
            "cabecalho": {
                "sistema": "INTELIGÊNCIA SINDICAL E FINANCEIRA ®",
                "modulo": "PONTE NACIONAL DE NORMAS",
                "data_emissao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "versao_estrutura": self.estrutura_padrao.versao_estrutura
            },
            "status_geral": resultado_validacao["status_validacao"],
            "resumo_analise": resultado_validacao["resumo"],
            "detalhes": {
                "clausulas_verificadas": resultado_validacao["lista_encontradas"],
                "clausulas_faltantes": resultado_validacao["lista_faltantes"],
                "alertas_consistencia": resultado_validacao.get("avisos", []) + resultado_validacao.get("erros", [])
            },
            "orientacao_envio": ""
        }

        # Define a orientação final
        if resultado_validacao["status_validacao"] == "✅ APROVADA":
            certificado["orientacao_envio"] = "📨 PODE ENVIAR: Documento em conformidade total com a legislação e padrões do MTE. Sem restrições."
        elif resultado_validacao["status_validacao"] == "⚠️ APROVADA COM RESSALVAS":
            certificado["orientacao_envio"] = "📝 REVISAR E ENVIAR: Documento tem pequenas pendências. Regularize os itens faltantes ou justifique no momento do registro."
        else:
            certificado["orientacao_envio"] = "🚫 NÃO ENVIAR: Pendências legais graves. O documento será rejeitado pelo sistema governamental. Corrija todas as cláusulas obrigatórias faltantes."

        # Salva em arquivo se caminho for informado
        if caminho_saida:
            try:
                with open(caminho_saida, 'w', encoding='utf-8') as f:
                    json.dump(certificado, f, indent=4, ensure_ascii=False)
                logger.info(f"Certificado salvo em: {caminho_saida}")
            except Exception as e:
                logger.error(f"Erro ao salvar certificado: {str(e)}")

        return certificado

    # ==================================================

    def executar_validacao_completa(self, dados_mapeados: Dict) -> Dict:
        """
        Fluxo completo: Verifica completude + Verifica consistência + Gera Certificado
        """
        logger.info("Iniciando validação completa da norma...")

        # 1. Verifica se tem tudo o que deve ter
        resultado_completude = self.verificar_completude(dados_mapeados)

        # 2. Verifica se os dados fazem sentido
        resultado_consistencia = self.verificar_consistencia_dados(dados_mapeados)
        resultado_completude["avisos"].extend(resultado_consistencia)

        # 3. Gera o certificado final
        certificado = self.gerar_certificado_conformidade(resultado_completude)

        return certificado

# ==================================================
# 🧪 TESTE COMPLETO DA VALIDAÇÃO
# ==================================================
if __name__ == "__main__":
    print("🔍 INICIANDO VALIDAÇÃO DE CONFORMIDADE...\n")

    # 1. Simulamos o resultado que veio do ConversorTexto
    # (Vamos usar o mesmo texto de exemplo do arquivo anterior)
    texto_teste = """
    CONVENÇÃO COLETIVA DE TRABALHO 2025/2026

    CLÁUSULA PRIMEIRA - VIGÊNCIA E DATA-BASE
    Período de 1º de janeiro de 2025 a 31 de dezembro de 2026.

    CLÁUSULA SEGUNDA - ABRANGÊNCIA
    Categoria de serviços gerais.

    CLÁUSULA TERCEIRA - PISO SALARIAL
    Valor de R$ 1.890,00.

    CLÁUSULA QUARTA - REAJUSTE SALARIAL
    Reajuste de 5,5%.
    """

    # 2. Processa o texto com o conversor
    conv = ConversorTexto()
    texto_limpo = conv.limpar_texto(texto_teste)
    estrutura_mapeada = conv.identificar_estrutura(texto_limpo)

    # 3. Instancia o validador e executa
    validador = ValidadorNormas()
    resultado_final = validador.executar_validacao_completa(estrutura_mapeada)

    # 4. EXIBE O RELATÓRIO FINAL
    print("="*80)
    print("📑 CERTIFICADO DE CONFORMIDADE - RELATÓRIO OFICIAL")
    print("="*80)
    print(json.dumps(resultado_final, indent=4, ensure_ascii=False))
    print("\n✅ Validação concluída!")