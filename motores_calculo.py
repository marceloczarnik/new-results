import json

def calcular_impacto_piso(salario_atual, piso_cct, percentual_encargos=40.0):
    """
    Módulo 4: Calcula a diferença entre o salário atual e o piso da CCT,
    projetando o impacto financeiro real com os encargos patronais.
    """
    # Tratamento para garantir que os valores sejam numéricos limpos
    try:
        if isinstance(piso_cct, str):
            # Limpa R$, pontos e substitui vírgula por ponto
            piso_limpo = piso_cct.replace("R$", "").replace(".", "").replace(",", ".").strip()
            piso_num = float(piso_limpo)
        else:
            piso_num = float(piso_cct)
            
        salario_num = float(salario_atual)
    except Exception as e:
        return {
            "erro": f"Falha ao processar valores numéricos para o cálculo: {e}",
            "reajuste_necessario": False
        }

    # Se o salário já for maior ou igual ao piso, não há impacto de reajuste obrigatório no piso base
    if salario_num >= piso_num:
        return {
            "reajuste_necessario": False,
            "diferenca_salarial": 0.0,
            "impacto_encargos": 0.0,
            "impacto_mensal_total": 0.0,
            "impacto_anual_total": 0.0,
            "mensagem": "O salário atual cumpre ou supera o piso estabelecido pela CCT."
        }

    # Cálculos Financeiros
    diferenca_base = piso_num - salario_num
    custo_encargos = diferenca_base * (percentual_encargos / 100.0)
    impacto_mensal = diferenca_base + custo_encargos
    
    # Projeção anual considerando 13º salário e o terço constitucional de férias (aproximadamente 13.33 folhas no ano)
    impacto_anual = impacto_mensal * 13.33

    return {
        "reajuste_necessario": True,
        "salario_atual": salario_num,
        "piso_direito": piso_num,
        "diferenca_salarial": round(diferenca_base, 2),
        "impacto_encargos": round(custo_encargos, 2),
        "impacto_mensal_total": round(impacto_mensal, 2),
        "impacto_anual_total": round(impacto_anual, 2),
        "percentual_aumento_direto": round((diferenca_base / salario_num) * 100, 2)
    }


def analisar_risco_clausulas(clausula_texto):
    """
    Módulo 5: Motor preditivo que varre o resumo de regras para identificar 
    gargalos e riscos de multas automáticas (ex: 10% do piso por infração).
    """
    risco_score = "Baixo"
    alertas = []
    
    texto_analise = clausula_texto.lower()
    
    # Regras de varredura lógica baseadas no que o Gemini extrai
    if "multa" in texto_analise or "penalidade" in texto_analise:
        risco_score = "Médio"
        alertas.append("⚠️ MULTA SINDICAL DETECTADA: Há penalidades expressas por descumprimento de cláusulas.")
        
    if "por empregado" in texto_analise or "por infração" in texto_analise:
        risco_score = "Alto"
        alertas.append("🚨 RISCO MULTIPLICADOR: As multas são cumulativas por trabalhador ou por mês afetado.")
        
    if "banco de horas" in texto_analise or "controle de jornada" in texto_analise:
        alertas.append("⏰ JORNADA FLEXÍVEL: Exige validação rigorosa de acordos coletivos ou Portaria do MTE para evitar passivos.")

    if not alertas:
        alertas.append("✅ Nenhuma cláusula crítica de alta penalidade financeira imediata foi mapeada no resumo.")

    return {
        "nivel_risco": risco_score,
        "alertas_identificados": alertas
    }


# Área de testes isolados do motor
if __name__ == "__main__":
    print("🧪 --- TESTANDO MOTORES DE CÁLCULO E ANÁLISE DE IMPACTO ---")
    
    # Cenário de Teste: Funcionário ganha R$ 1.600,00 e o piso do SIEMACO é R$ 2.041,00
    salario_teste = 1600.00
    piso_teste = "R$ 2.041,00"
    encargos_empresa = 60.0  # Exemplo: 60% de carga de encargos (Lucro Presumido/Real comum)
    
    print(f"\n📊 Cenário: Salário Atual R$ {salario_teste} vs Piso CCT {piso_teste} (Encargos: {encargos_empresa}%)")
    resultado_financeiro = calcular_impacto_piso(salario_teste, piso_teste, encargos_empresa)
    
    print(json.dumps(resultado_financeiro, indent=4, ensure_ascii=False))
    
    # Teste de risco de cláusula (Simulando o retorno que tivemos do SIEMACO)
    texto_exemplo_siemaco = "Penalidades: O descumprimento de qualquer cláusula sujeita o infrator a uma multa de 10% do menor piso salarial por infração e por empregado prejudicado."
    
    print("\n⚡ Analisando riscos preditivos do texto da cláusula...")
    analise_risco = analisar_risco_clausulas(texto_exemplo_siemaco)
    print(json.dumps(analise_risco, indent=4, ensure_ascii=False))