import json
import os

class EngineEnquadramentoTrabalhista:
    def __init__(self, caminho_json: str):
        self.caminho_json = caminho_json
        self.regras = self._carregar_regras()

    def _carregar_regras(self):
        """Carrega as regras do arquivo JSON com tratamento de erros."""
        if not os.path.exists(self.caminho_json):
            return {}
        try:
            with open(self.caminho_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def analisar_folha_pagamento(self, funcionarios: list) -> dict:
        """
        Varre a lista de funcionários avaliando CBOs e cargos para identificar
        a necessidade de enquadramento em CCTs Satélites.
        """
        sindicatos_satelites = set()
        funcionarios_especiais = []

        mapeamento_cbo = self.regras.get("mapeamento_cbo", {
            "7823": "Sindicato dos Motoristas",
            "7824": "Sindicato dos Motoristas",
            "7825": "Sindicato dos Motoristas",
            "5173": "Sindicato dos Vigilantes",
            "7156": "Sindicato dos Eletricistas",
            "9511": "Sindicato dos Eletricistas"
        })

        for func in funcionarios:
            cbo = str(func.get("cbo", "")).strip()
            cargo = str(func.get("cargo", "")).lower()
            id_func = func.get("id")
            nome = func.get("nome")

            enquadrado = False
            sindicato_alvo = None

            for cbo_regra, sindicato in mapeamento_cbo.items():
                if cbo.startswith(cbo_regra):
                    sindicato_alvo = sindicato
                    enquadrado = True
                    break

            if not enquadrado:
                if "motorista" in cargo or "condutor" in cargo:
                    sindicato_alvo = "Sindicato dos Motoristas"
                    enquadrado = True
                elif "vigilante" in cargo or "vigia" in cargo or "seguranca" in cargo:
                    sindicato_alvo = "Sindicato dos Vigilantes"
                    enquadrado = True
                elif "eletricista" in cargo or "eletrotecnico" in cargo:
                    sindicato_alvo = "Sindicato dos Eletricistas"
                    enquadrado = True

            if enquadrado and sindicato_alvo:
                sindicatos_satelites.add(sindicato_alvo)
                funcionarios_especiais.append({
                    "id": id_func,
                    "nome": nome,
                    "cargo": func.get("cargo"),
                    "cbo": cbo,
                    "sindicato_satelite_identificado": sindicato_alvo
                })

        return {
            "total_funcionarios_analisados": len(funcionarios),
            "total_categorias_especiais_encontradas": len(funcionarios_especiais),
            "sindicatos_satelites_obrigatorios": list(sindicatos_satelites),
            "detalhe_funcionarios_especiais": funcionarios_especiais
        }