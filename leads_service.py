from config_banco import conectar_banco as abrir_banco


def salvar_lead_comercial(nome, email, whatsapp, plano_interesse, origem_tela, cidade, uf, cnae):
    """Persiste lead comercial para funil de conversão do produto."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()
    cursor_local.execute(
        """
        INSERT INTO leads_comerciais (
            nome, email, whatsapp, plano_interesse,
            status_atendimento, origem_tela, cidade_contexto, uf_contexto, cnae_contexto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            email,
            whatsapp,
            plano_interesse,
            "NOVO",
            origem_tela,
            cidade,
            uf,
            cnae,
        ),
    )
    conn_local.commit()
    conn_local.close()


def carregar_leads(planos=None, status=None, busca_nome="", data_inicial=None, data_final=None):
    """Retorna leads filtrados para operação comercial."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    query = """
        SELECT id, nome, plano_interesse, status_atendimento, email, whatsapp,
               cidade_contexto, uf_contexto, cnae_contexto, origem_tela, data_criacao
        FROM leads_comerciais
        WHERE 1 = 1
    """
    params = []

    if planos:
        placeholders = ",".join(["?"] * len(planos))
        query += f" AND plano_interesse IN ({placeholders})"
        params.extend(planos)

    if status:
        placeholders = ",".join(["?"] * len(status))
        query += f" AND status_atendimento IN ({placeholders})"
        params.extend(status)

    if busca_nome:
        query += " AND nome LIKE ?"
        params.append(f"%{busca_nome}%")

    if data_inicial:
        query += " AND date(data_criacao) >= date(?)"
        params.append(str(data_inicial))

    if data_final:
        query += " AND date(data_criacao) <= date(?)"
        params.append(str(data_final))

    query += " ORDER BY id DESC"
    cursor_local.execute(query, params)
    linhas = cursor_local.fetchall()
    conn_local.close()
    return linhas


def atualizar_status_lead(lead_id, novo_status, alterado_por="Equipe Comercial", observacao=""):
    """Atualiza o status de atendimento de um lead comercial."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    cursor_local.execute(
        "SELECT status_atendimento FROM leads_comerciais WHERE id = ?",
        (int(lead_id),),
    )
    linha = cursor_local.fetchone()
    status_anterior = linha[0] if linha else None

    if not linha:
        conn_local.close()
        return 0

    if status_anterior == novo_status:
        conn_local.close()
        return 0

    cursor_local.execute(
        "UPDATE leads_comerciais SET status_atendimento = ? WHERE id = ?",
        (novo_status, int(lead_id)),
    )
    alterados = cursor_local.rowcount

    if alterados:
        cursor_local.execute(
            """
            INSERT INTO leads_movimentacoes (
                lead_id, status_anterior, status_novo, alterado_por, observacao
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(lead_id),
                status_anterior,
                novo_status,
                alterado_por,
                observacao,
            ),
        )

    conn_local.commit()
    conn_local.close()
    return alterados


def carregar_historico_movimentacoes(lead_id=None, limite=100):
    """Carrega histórico de mudanças de status dos leads."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    if lead_id:
        cursor_local.execute(
            """
            SELECT m.id, m.lead_id, l.nome, m.status_anterior, m.status_novo,
                   m.alterado_por, m.observacao, m.data_movimentacao
            FROM leads_movimentacoes m
            JOIN leads_comerciais l ON l.id = m.lead_id
            WHERE m.lead_id = ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (int(lead_id), int(limite)),
        )
    else:
        cursor_local.execute(
            """
            SELECT m.id, m.lead_id, l.nome, m.status_anterior, m.status_novo,
                   m.alterado_por, m.observacao, m.data_movimentacao
            FROM leads_movimentacoes m
            JOIN leads_comerciais l ON l.id = m.lead_id
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (int(limite),),
        )

    linhas = cursor_local.fetchall()
    conn_local.close()
    return linhas


def carregar_alertas_sla(horas_limite=48, data_inicial=None, data_final=None):
    """Retorna leads em NOVO acima do limite de horas para SLA."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    query = """
        SELECT id, nome, plano_interesse, email, whatsapp,
               ROUND((julianday('now') - julianday(data_criacao)) * 24, 1) AS horas_em_aberto,
               data_criacao
        FROM leads_comerciais
        WHERE status_atendimento = 'NOVO'
          AND ((julianday('now') - julianday(data_criacao)) * 24) >= ?
    """
    params = [float(horas_limite)]

    if data_inicial:
        query += " AND date(data_criacao) >= date(?)"
        params.append(str(data_inicial))

    if data_final:
        query += " AND date(data_criacao) <= date(?)"
        params.append(str(data_final))

    query += " ORDER BY horas_em_aberto DESC"
    cursor_local.execute(query, params)
    linhas = cursor_local.fetchall()
    conn_local.close()
    return linhas


def carregar_metricas_performance(data_inicial=None, data_final=None):
    """Calcula métricas comerciais por período (entradas, conversões e tempo médio por etapa)."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    filtro_leads = " WHERE 1 = 1 "
    params_leads = []

    if data_inicial:
        filtro_leads += " AND date(data_criacao) >= date(?)"
        params_leads.append(str(data_inicial))
    if data_final:
        filtro_leads += " AND date(data_criacao) <= date(?)"
        params_leads.append(str(data_final))

    cursor_local.execute(f"SELECT COUNT(*) FROM leads_comerciais {filtro_leads}", params_leads)
    entradas = cursor_local.fetchone()[0]

    cursor_local.execute(
        f"SELECT COUNT(*) FROM leads_comerciais {filtro_leads} AND status_atendimento = 'GANHO'",
        params_leads,
    )
    ganhos = cursor_local.fetchone()[0]

    taxa_conversao = round((ganhos / entradas) * 100, 2) if entradas else 0.0

    filtro_mov = " WHERE 1 = 1 "
    params_mov = []
    if data_inicial:
        filtro_mov += " AND date(m.data_movimentacao) >= date(?)"
        params_mov.append(str(data_inicial))
    if data_final:
        filtro_mov += " AND date(m.data_movimentacao) <= date(?)"
        params_mov.append(str(data_final))

    cursor_local.execute(
        f"""
        SELECT m.status_novo,
               ROUND(AVG((julianday(m.data_movimentacao) - julianday(l.data_criacao)) * 24), 2) AS horas_medias
        FROM leads_movimentacoes m
        JOIN leads_comerciais l ON l.id = m.lead_id
        {filtro_mov}
        GROUP BY m.status_novo
        ORDER BY m.status_novo
        """,
        params_mov,
    )
    tempo_medio_etapas = cursor_local.fetchall()

    cursor_local.execute(
        f"""
        SELECT m.status_novo, COUNT(*)
        FROM leads_movimentacoes m
        {filtro_mov}
        GROUP BY m.status_novo
        ORDER BY COUNT(*) DESC
        """,
        params_mov,
    )
    distribuicao_etapas = cursor_local.fetchall()

    conn_local.close()
    return {
        "entradas": entradas,
        "ganhos": ganhos,
        "taxa_conversao": taxa_conversao,
        "tempo_medio_etapas": tempo_medio_etapas,
        "distribuicao_etapas": distribuicao_etapas,
    }


def carregar_metricas_por_plano(data_inicial=None, data_final=None):
    """Retorna métricas de conversão segmentadas por plano."""
    conn_local = abrir_banco()
    cursor_local = conn_local.cursor()

    filtro = " WHERE 1 = 1 "
    params = []
    if data_inicial:
        filtro += " AND date(data_criacao) >= date(?)"
        params.append(str(data_inicial))
    if data_final:
        filtro += " AND date(data_criacao) <= date(?)"
        params.append(str(data_final))

    cursor_local.execute(
        f"""
        SELECT plano_interesse,
               COUNT(*) AS entradas,
               SUM(CASE WHEN status_atendimento = 'GANHO' THEN 1 ELSE 0 END) AS ganhos
        FROM leads_comerciais
        {filtro}
        GROUP BY plano_interesse
        """,
        params,
    )
    linhas = cursor_local.fetchall()
    conn_local.close()
    return linhas
