import json

from config_banco import conectar_banco as abrir_banco
import core.painel_helpers as painel_helpers


resolver_entidades_cct = getattr(
    painel_helpers,
    "resolver_entidades_cct",
    lambda patronal, laboral, _arquivo: (patronal or "Não Informado", laboral or "Não Informado"),
)


def _normalizar_valor_campo(valor):
    if valor is None:
        return ""
    if isinstance(valor, list):
        partes = [str(item).strip() for item in valor if str(item).strip()]
        return ", ".join(partes)
    if isinstance(valor, dict):
        partes = [f"{chave}: {conteudo}" for chave, conteudo in valor.items() if str(conteudo).strip()]
        return " | ".join(partes)
    return str(valor).strip()


def _extrair_campo_dados_completos(dados_completos, chaves, fallback):
    for chave in chaves:
        valor = _normalizar_valor_campo(dados_completos.get(chave))
        if valor:
            return valor
    return fallback


def buscar_retorno_por_instrumento(instrumento):
    """Busca dados de enquadramento para o instrumento escolhido no fluxo manual."""
    if not instrumento:
        return None

    sid = instrumento.get("id")
    fonte = instrumento.get("fonte")

    if not sid or not fonte:
        return None

    conn = abrir_banco()
    cursor = conn.cursor()

    retorno_motor = None

    if fonte == "sindicatos":
        cursor.execute(
            """
            SELECT id, sindicato_patronal, sindicato_laboral, vigencia,
                   piso_salarial, reajuste_salarial, vale_refeicao, auxilio_creche, clausula_critica, NULL
            FROM sindicatos WHERE id = ?
            """,
            (sid,),
        )
        r = cursor.fetchone()
        if r:
            retorno_motor = {
                "principais": [
                    {
                        "id": r[0],
                        "patronal": r[1] or "Não Informado",
                        "laboral": r[2] or "Não Informado",
                        "vigencia": r[3] or "Não Especificada",
                        "piso": r[4] or "Ver na íntegra",
                        "reajuste": r[5] or "Consta no relatório",
                        "va": r[6] or "Consta no relatório",
                        "creche": r[7] or "Consta no relatório",
                        "critica": r[8] or "Nenhuma cláusula crítica reportada.",
                        "dados_completo": "",
                    }
                ],
                "satelites": [],
            }
    else:
        cursor.execute(
            """
            SELECT id, id_entidade_patronal, id_entidade_sindical,
                   vigencia_inicio || ' até ' || vigencia_fim,
                   piso_salarial, NULL, NULL, NULL, clausula_critica, dados_completos, arquivo_origem
            FROM ccts WHERE id = ?
            """,
            (sid,),
        )
        r = cursor.fetchone()
        if r:
            patronal_resolvido, laboral_resolvido = resolver_entidades_cct(r[1], r[2], r[10])
            try:
                dados_completos = json.loads(r[9]) if r[9] else {}
            except (TypeError, json.JSONDecodeError):
                dados_completos = {}

            reajuste = _extrair_campo_dados_completos(
                dados_completos,
                ["reajuste_salarial", "reajuste", "percentual_reajuste", "indice_reajuste"],
                "Não extraído do instrumento coletivo",
            )
            vale_refeicao = _extrair_campo_dados_completos(
                dados_completos,
                ["vale_refeicao", "vale_refeicao_descricao", "vale_alimentacao", "vale_alimentacao_descricao"],
                "Não extraído do instrumento coletivo",
            )
            auxilio_creche = _extrair_campo_dados_completos(
                dados_completos,
                ["auxilio_creche", "auxilio_creche_descricao", "creche", "beneficio_creche"],
                "Não extraído do instrumento coletivo",
            )
            retorno_motor = {
                "principais": [
                    {
                        "id": r[0],
                        "patronal": patronal_resolvido,
                        "laboral": laboral_resolvido,
                        "vigencia": r[3] or "Não Especificada",
                        "piso": r[4] or "Ver na íntegra",
                        "reajuste": reajuste,
                        "va": vale_refeicao,
                        "creche": auxilio_creche,
                        "critica": r[8] or "Nenhuma cláusula crítica reportada.",
                        "dados_completo": r[9] or "",
                    }
                ],
                "satelites": [],
            }

    conn.close()
    return retorno_motor
