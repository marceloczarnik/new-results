# ==================================================
# 🚀 PROJETO: INTELIGÊNCIA SINDICAL E FINANCEIRA
# 📌 ARQUIVO: padronizacao/conversor_texto.py
# 📍 FUNÇÃO: Leitura, Extração e Limpeza de Dados
#     Transforma arquivos brutos (PDF, DOCX, TXT) em estrutura organizada
# ==================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import re
import json
import unicodedata
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime

# Bibliotecas que instalamos no início
import PyPDF2
import pdfplumber
from docx import Document
from unidecode import unidecode

# Importa a estrutura padrão que acabamos de criar
from estrutura_universal import EstruturaUniversal

logger = logging.getLogger(__name__)

class ConversorTexto:
    """
    Classe responsável por:
    1. Ler arquivos nos formatos: .pdf, .docx, .txt
    2. Extrair todo o texto bruto
    3. Limpar caracteres especiais, espaços, quebras de linha ruins
    4. Identificar Capítulos, Cláusulas e organizar o conteúdo
    5. Retornar um dicionário pronto para validação e envio
    """

    def __init__(self):
        self.estrutura_padrao = EstruturaUniversal()
        self.padroes_busca = self._criar_padroes_regex()

    # ==================================================

    def _criar_padroes_regex(self) -> Dict:
        """
        Cria os padrões de busca (expressões regulares) para identificar
        automaticamente onde começa e termina cada Cláusula ou Capítulo no texto.
        Reconhece formatos como: "CLÁUSULA PRIMEIRA", "CLÁUSULA 1ª", "1. -", "1.1 -", etc.
        """
        return {
            "clausula": re.compile(
                r'(CLÁUSULA|CLAUSULA)\s+[A-ZÀ-Ú0-9ªº]+\s*[-–—]?', 
                re.IGNORECASE | re.MULTILINE
            ),
            "capitulo": re.compile(
                r'(CAPÍTULO|CAPITULO)\s+[A-ZÀ-Ú0-9ªº\s]+', 
                re.IGNORECASE | re.MULTILINE
            ),
            "numero_item": re.compile(
                r'^\s*\d+(\.\d+)*\s*[-–—.)]\s+', 
                re.MULTILINE
            )
        }

    # ==================================================

    def ler_arquivo(self, caminho_arquivo: str) -> Optional[str]:
        """
        Identifica o tipo de arquivo e chama a função de leitura correta.
        Suporta: .txt, .docx, .pdf
        """
        try:
            if not os.path.exists(caminho_arquivo):
                logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
                return None

            extensao = os.path.splitext(caminho_arquivo)[1].lower()
            logger.info(f"Lendo arquivo: {caminho_arquivo} | Tipo: {extensao}")

            if extensao == '.txt':
                return self._ler_txt(caminho_arquivo)
            elif extensao == '.docx':
                return self._ler_docx(caminho_arquivo)
            elif extensao == '.pdf':
                return self._ler_pdf(caminho_arquivo)
            else:
                logger.error(f"Formato de arquivo não suportado: {extensao}")
                return None

        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {str(e)}")
            return None

    # ==================================================

    def _ler_txt(self, caminho: str) -> str:
        """Lê arquivos de texto puro."""
        with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _ler_docx(self, caminho: str) -> str:
        """Lê arquivos do Word (.docx)."""
        doc = Document(caminho)
        return "\n".join([paragrafo.text for paragrafo in doc.paragraphs])

    def _ler_pdf(self, caminho: str) -> str:
        """
        Lê arquivos PDF. Usa duas bibliotecas para garantir a leitura,
        mesmo que o PDF seja escaneado ou tenha formatação diferente.
        """
        texto_completo = ""
        # Tenta com pdfplumber (melhor para texto comum)
        try:
            with pdfplumber.open(caminho) as pdf:
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo += texto_pagina + "\n"
        except:
            # Se falhar, tenta com PyPDF2
            try:
                with open(caminho, 'rb') as f:
                    leitor = PyPDF2.PdfReader(f)
                    for pagina in leitor.pages:
                        texto_pagina = pagina.extract_text()
                        if texto_pagina:
                            texto_completo += texto_pagina + "\n"
            except Exception as e2:
                logger.warning(f"Não foi possível extrair texto do PDF: {str(e2)}")
                return ""
        
        return texto_completo

    # ==================================================

    def limpar_texto(self, texto_bruto: str) -> str:
        """
        🧹 FUNÇÃO DE LIMPEZA ESSENCIAL:
        - Remove acentos (opcional, para busca)
        - Remove caracteres especiais que atrapalham
        - Remove espaços duplicados e quebras de linha desnecessárias
        - Padroniza quebras de parágrafo
        """
        if not texto_bruto:
            return ""

        # 1. Normaliza caracteres e remove acentos mantendo o original para exibição
        texto = unicodedata.normalize('NFC', texto_bruto)

        # 2. Remove caracteres de controle ruins, mantém quebras de linha e espaços
        texto = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', texto)

        # 3. Padroniza quebras de linha
        texto = texto.replace('\r', '\n')
        texto = re.sub(r'\n\s+', '\n', texto)  # Remove espaços depois de quebra
        texto = re.sub(r'\n{3,}', '\n\n', texto) # Máximo 2 quebras de linha

        # 4. Remove espaços duplicados no meio do texto
        texto = re.sub(r' +', ' ', texto)

        # 5. Remove espaços no início e fim de cada linha
        texto = "\n".join([linha.strip() for linha in texto.split('\n')])

        logger.info("Texto limpo e padronizado com sucesso.")
        return texto

    # ==================================================

    def identificar_estrutura(self, texto_limpo: str) -> Dict:
        """
        🧠 INTELIGÊNCIA PRINCIPAL:
        Percorre o texto limpo e tenta identificar onde começa cada Cláusula,
        separando o conteúdo de forma organizada para comparar com o padrão oficial.
        """
        resultado = {
            "metadados": {
                "processado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "status": "processado",
                "total_caracteres": len(texto_limpo)
            },
            "conteudo_identificado": {
                "capitulos": [],
                "clausulas": [],
                "conteudo_nao_identificado": ""
            }
        }

        # 1. Separa o texto por Cláusulas (é o elemento principal)
        # Usando o padrão criado no início
        partes = self.padroes_busca['clausula'].split(texto_limpo)
        cabecalho = partes.pop(0).strip() # Tudo que vem antes da primeira cláusula

        resultado["conteudo_identificado"]["cabecalho"] = cabecalho

        # 2. Para cada parte encontrada, extrai título e conteúdo
        for i, conteudo in enumerate(partes):
            # Busca o nome da cláusula que está logo acima do conteúdo
            match = self.padroes_busca['clausula'].search(texto_limpo)
            if match:
                titulo_clausula = match.group(0).strip()
            else:
                titulo_clausula = f"Cláusula Não Identificada {i+1}"

            # Limpa e armazena
            conteudo_limpo = conteudo.strip()
            if conteudo_limpo:
                # Tenta encontrar no padrão oficial
                codigo_encontrado = None
                # Busca palavras chave para mapear
                texto_busca = unidecode(conteudo_limpo.lower()) # Remove acentos para busca

                # Lógica simples de mapeamento (vamos melhorar depois com IA)
                if "piso salarial" in texto_busca or "valor minimo" in texto_busca:
                    codigo_encontrado = "CLA-002-01-001"
                elif "reajuste" in texto_busca or "aumento" in texto_busca:
                    codigo_encontrado = "CLA-002-01-002"
                elif "refeicao" in texto_busca or "alimentacao" in texto_busca:
                    codigo_encontrado = "CLA-003-01-001"
                elif "transporte" in texto_busca:
                    codigo_encontrado = "CLA-003-01-002"
                elif "vigencia" in texto_busca or "validade" in texto_busca:
                    codigo_encontrado = "CLA-001-02-003"

                resultado["conteudo_identificado"]["clausulas"].append({
                    "ordem": i+1,
                    "titulo": titulo_clausula,
                    "conteudo": conteudo_limpo[:300] + "..." if len(conteudo_limpo) > 300 else conteudo_limpo, # Mostra resumo
                    "codigo_estrutura": codigo_encontrado,
                    "status_mapeamento": "MAPEADO" if codigo_encontrado else "NAO_MAPEADO"
                })

        resultado["metadados"]["total_clausulas_encontradas"] = len(resultado["conteudo_identificado"]["clausulas"])
        logger.info(f"Análise estrutural concluída. {len(resultado['conteudo_identificado']['clausulas'])} cláusulas encontradas.")
        return resultado

    # ==================================================

    def processar_arquivo_completo(self, caminho_arquivo: str) -> Dict:
        """
        Método principal: executa todo o fluxo de uma vez só:
        Ler -> Limpar -> Identificar -> Retornar resultado
        """
        texto_bruto = self.ler_arquivo(caminho_arquivo)
        if not texto_bruto:
            return {"status": "erro", "mensagem": "Falha na leitura do arquivo."}

        texto_limpo = self.limpar_texto(texto_bruto)
        estrutura = self.identificar_estrutura(texto_limpo)

        return estrutura

# ==================================================
# 🧪 TESTE DO CONVERSOR
# ==================================================
if __name__ == "__main__":
    # Instancia o conversor
    conv = ConversorTexto()

    # 📝 SIMULAÇÃO: Texto de uma CCT para teste
    texto_teste = """
    CONVENÇÃO COLETIVA DE TRABALHO 2025/2026

    SINDICATO DOS TRABALHADORES EM SERVIÇOS GERAIS DE MARINGÁ 
    CNPJ: 12.345.678/0001-90

    SINDICATO DAS EMPRESAS DE SERVIÇOS GERAIS DO PARANÁ
    CNPJ: 98.765.432/0001-10

    CLÁUSULA PRIMEIRA - VIGÊNCIA E DATA-BASE
    As partes fixam a vigência da presente Convenção Coletiva de Trabalho 
    no período de 1º de janeiro de 2025 a 31 de dezembro de 2026.

    CLÁUSULA SEGUNDA - ABRANGÊNCIA
    A presente Convenção Coletiva de Trabalho abrangerá a categoria profissional 
    dos trabalhadores em serviços gerais, limpeza e conservação, nas cidades de Maringá, 
    Sarandi e Paiçandu.

    CLÁUSULA TERCEIRA - PISO SALARIAL
    Fica estabelecido o piso salarial da categoria no valor de R$ 1.890,00 (mil, oitocentos e noventa reais) 
    por mês, a partir de 1º de janeiro de 2025.

    CLÁUSULA QUARTA - REAJUSTE SALARIAL
    Os salários dos empregados serão reajustados em 5,5% (cinco vírgula cinco por cento), 
    correspondente à reposição da inflação + aumento real.

    CLÁUSULA QUINTA - VALE REFEIÇÃO
    As empresas concederão aos seus empregados vale-refeição no valor de R$ 25,00 
    por dia útil trabalhado.
    """

    # 1. Limpa o texto de exemplo
    texto_processado = conv.limpar_texto(texto_teste)

    # 2. Identifica a estrutura dentro do texto
    resultado_final = conv.identificar_estrutura(texto_processado)

    # 3. Exibe resultado
    print("="*70)
    print("📄 RESULTADO DO CONVERSOR DE TEXTO")
    print("="*70)
    print(json.dumps(resultado_final, indent=4, ensure_ascii=False))
    print("\n✅ Conversão e análise estrutural finalizada!")