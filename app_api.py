from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os  # Adicionado para gerenciar caminhos de arquivos de forma robusta

# Importamos a classe que criamos na conversa anterior
from enquadramento import EngineEnquadramentoTrabalhista

app = FastAPI(
    title="API de Compliance e Enquadramento de Convenções Coletivas",
    description="API para análise profunda de folhas de pagamento e identificação de CCTs Satélites.",
    version="1.0.0"
)

# 1. Definição do modelo de dados que o seu site/front-end vai enviar (Segurança de Dados)
class FuncionarioSchema(BaseModel):
    id: int
    nome: str
    cargo: str
    cbo: str

class FolhaPagamentoRequest(BaseModel):
    empresa_cnpj: str
    funcionarios: List[FuncionarioSchema]

# 2. Inicializa o motor de enquadramento apontando dinamicamente para o nosso JSON
# Descobre o caminho absoluto do diretório onde este arquivo (app_api.py) está localizado
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_json = os.path.join(diretorio_atual, "categorias_especiais.json")

try:
    motor_compliance = EngineEnquadramentoTrabalhista(caminho_json)
except Exception as e:
    # Caso ocorra qualquer problema na leitura inicial do arquivo
    motor_compliance = None

@app.post("/api/v1/analisar-folha", summary="Analisa a folha de pagamento buscando categorias especiais")
async def analisar_folha(payload: FolhaPagamentoRequest):
    """
    Esta rota recebe o CNPJ e a lista de funcionários com CBOs.
    Ela processa os dados através do arquivo determinístico e aponta 
    quais sindicatos satélites a IA profunda deve ler.
    """
    if not motor_compliance:
        raise HTTPException(
            status_code=500, 
            detail=f"Base de dados 'categorias_especiais.json' não pôde ser carregada em: {caminho_json}"
        )
    
    # Convertendo o payload para dicionário de forma compatível com Pydantic v1 e v2
    funcionarios_dict = [
        func.model_dump() if hasattr(func, "model_dump") else func.dict() 
        for func in payload.funcionarios
    ]
    
    # Executa a inteligência de enquadramento
    diagnostico = motor_compliance.analisar_folha_pagamento(funcionarios_dict)
    
    # Garante que a chave exista no retorno do diagnóstico para evitar quebras de string
    satelites_identificados = diagnostico.get('sindicatos_satelites_obrigatorios', [])
    
    resposta_final = {
        "cnpj_empresa_analisada": payload.empresa_cnpj,
        "status_compliance": "Analise Concluída",
        "diagnostico_categorias_especiais": diagnostico,
        "proximos_passos_ia": f"A IA executará agora a leitura aprofundada nos PDFs dos sindicatos: {satelites_identificados} para extrair os pisos salariais vigentes."
    }
    
    return resposta_final

# Para rodar este servidor no VS Code, execute no terminal da raiz do projeto:
# uvicorn app_api:app --reload