"""Camada de acesso a dados.

B2 - Consultas parametrizadas e tratamento de erro de restricao.

Regras seguidas neste modulo:

1. Todo valor vindo do usuario viaja como PARAMETRO, nunca concatenado no SQL.
   A unica coisa que a aplicacao monta dinamicamente e a lista de colunas de um
   UPDATE, e mesmo assim os nomes de coluna sao validados contra uma lista
   fechada definida no codigo (COLUNAS_PERMITIDAS). Nenhum texto digitado pelo
   usuario chega a fazer parte do comando SQL.

2. Erros de restricao do banco sao traduzidos para mensagem de usuario por
   traduz_erro(). A excecao bruta do driver nunca chega a tela.
"""

from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector
from mysql.connector import errorcode

import config


def dinheiro(valor) -> Decimal:
    """Arredonda para 2 casas usando Decimal, nunca float.

    Motivo (aprendido na marra durante os testes): as colunas financeiras sao
    DECIMAL(14,2) e o banco tem a restricao

        ck_prestacao_saldo CHECK (saldo = total_bruto - total_descontos)

    que e avaliada em aritmetica decimal exata. Calculando em float, o desconto
    de 5% sobre 52.751.785,73 chega ao banco com um residuo binario invisivel,
    e a subtracao feita pelo MySQL nao bate com o saldo que enviamos - a
    restricao reprova a gravacao. Com Decimal, a conta do Python e a conta do
    banco sao a mesma. Dinheiro nao se calcula em ponto flutuante.
    """
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Conexao
# ---------------------------------------------------------------------------
@contextmanager
def conexao(perfil: str):
    """Abre conexao com a conta de banco correspondente ao perfil.

    autocommit fica DESLIGADO de proposito: as operacoes de escrita desta
    aplicacao sao transacionais e o commit e explicito.
    """
    conta = config.CONTAS[perfil]
    con = mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=conta["user"],
        password=conta["password"],
        autocommit=False,
    )
    try:
        yield con
    finally:
        con.close()


def consulta(perfil, sql, params=()):
    """SELECT parametrizado. Devolve lista de dicionarios."""
    with conexao(perfil) as con:
        cur = con.cursor(dictionary=True, prepared=True)
        cur.execute(sql, params)
        linhas = cur.fetchall()
        cur.close()
        return linhas


def executa(perfil, sql, params=()):
    """INSERT/UPDATE/DELETE parametrizado, com commit. Devolve linhas afetadas."""
    with conexao(perfil) as con:
        cur = con.cursor(prepared=True)
        cur.execute(sql, params)
        afetadas = cur.rowcount
        ultimo_id = cur.lastrowid
        con.commit()
        cur.close()
        return afetadas, ultimo_id


# ---------------------------------------------------------------------------
# Traducao de erro do banco para mensagem de usuario
# ---------------------------------------------------------------------------
# Cada restricao nomeada no DDL da Etapa 1 recebe aqui uma frase que explica o
# problema no vocabulario do dominio. A chave e o nome da restricao, por isso a
# convencao de nomes adotada na Etapa 1 (pk_/uq_/fk_/ck_) paga dividendo agora:
# da para mapear a mensagem sem depender do texto do driver.
MENSAGENS_RESTRICAO = {
    "uq_associado_matricula": "Ja existe um associado com essa matricula.",
    "uq_associado_pf_cpf": "Esse CPF ja esta cadastrado para outro associado.",
    "uq_associado_pj_cnpj": "Esse CNPJ ja esta cadastrado para outro associado.",
    "uq_propriedade_registro": "Ja existe uma propriedade com esse registro rural.",
    "uq_cultura_nome": "Ja existe uma cultura com esse nome.",
    "uq_safra_descricao": "Ja existe uma safra com essa descricao.",
    "uq_prestacao_associado_safra": "Esse associado ja tem prestacao de contas nesta safra.",
    "uq_movimento_referencia": "Ja existe um movimento financeiro com essa referencia.",
    "ck_associado_tipo": "Tipo de pessoa deve ser PF ou PJ.",
    "ck_associado_status": "Status deve ser ATIVO, SUSPENSO ou INATIVO.",
    "ck_propriedade_area": "A area da propriedade precisa ser maior que zero.",
    "ck_propriedade_status": "Status da propriedade invalido.",
    "ck_safra_periodo": "A data final da safra precisa ser posterior a inicial.",
    "ck_safra_status": "Status da safra invalido.",
    "ck_lote_numero": "O numero do lote precisa ser maior que zero.",
    "ck_lote_quantidade": "A quantidade planejada precisa ser maior que zero.",
    "ck_lote_status": "Status do lote invalido.",
    "ck_entrega_quantidade": "A quantidade entregue precisa ser maior que zero.",
    "ck_entrega_qualidade": "A qualidade precisa ser A, B ou C.",
    "ck_entrega_preco": "O preco por quilo precisa ser maior que zero.",
    "ck_entrega_status": "Status da entrega invalido.",
    "ck_prestacao_descontos": "Os descontos nao podem superar o valor bruto.",
    "ck_prestacao_saldo": "O saldo precisa ser igual ao bruto menos os descontos.",
    "ck_movimento_valor": "O valor do movimento precisa ser maior que zero.",
    "ck_movimento_tipo": "O tipo do movimento deve ser CREDITO ou DEBITO.",
    "fk_propriedade_associado": "Associado informado nao existe.",
    "fk_lote_propriedade": "Propriedade informada nao existe.",
    "fk_lote_cultura": "Cultura informada nao existe.",
    "fk_entrega_lote": "O lote informado nao existe nessa safra.",
    "fk_movimento_prestacao": "A prestacao de contas informada nao existe.",
}


def traduz_erro(erro: Exception) -> str:
    """Converte a excecao do driver em frase compreensivel.

    A aplicacao nunca mostra o texto cru do MySQL ao usuario: alem de ser
    incompreensivel para quem opera a cooperativa, ele revela nomes de tabela e
    estrutura interna, o que e informacao util para quem tenta atacar o sistema.
    """
    if not isinstance(erro, mysql.connector.Error):
        return "Nao foi possivel concluir a operacao."

    texto = str(erro)

    # Procura o nome da restricao dentro da mensagem do driver.
    for nome, frase in MENSAGENS_RESTRICAO.items():
        if nome in texto:
            return frase

    codigo = getattr(erro, "errno", None)

    if codigo == errorcode.ER_DUP_ENTRY:
        return "Esse registro ja existe (valor duplicado em campo unico)."
    # 1217 (ER_ROW_IS_REFERENCED) e 1451 (ER_ROW_IS_REFERENCED_2) descrevem a
    # mesma situacao. Qual dos dois o servidor devolve depende de como a
    # violacao foi detectada; na pratica e preciso tratar os dois. Descobrimos
    # isso no teste: esperavamos 1451 e o MySQL 8.0 devolveu 1217.
    if codigo in (1217, errorcode.ER_ROW_IS_REFERENCED_2):
        return ("Nao da para remover: existem registros dependentes ligados a "
                "este. Remova ou transfira os dependentes antes.")
    if codigo in (1216, errorcode.ER_NO_REFERENCED_ROW_2):
        return "Um dos registros relacionados informados nao existe."
    if codigo == errorcode.ER_BAD_NULL_ERROR:
        return "Um campo obrigatorio ficou em branco."
    if codigo == errorcode.ER_TABLEACCESS_DENIED_ERROR or codigo == 1142:
        return ("Seu perfil de acesso nao permite esta operacao. "
                "Entre com um perfil autorizado.")
    if codigo == 3819:  # ER_CHECK_CONSTRAINT_VIOLATED
        return "Os dados informados violam uma regra de validacao do cadastro."
    if codigo == 1205:  # ER_LOCK_WAIT_TIMEOUT
        return ("Outro usuario esta alterando este mesmo registro. "
                "Aguarde alguns instantes e tente de novo.")
    if codigo == 1213:  # ER_LOCK_DEADLOCK
        return ("Houve conflito com outra operacao simultanea e esta foi "
                "desfeita. Tente novamente.")

    return "Nao foi possivel concluir a operacao com os dados informados."


# ---------------------------------------------------------------------------
# CRUD generico sobre lista fechada de entidades
# ---------------------------------------------------------------------------
# Cada entidade declara sua tabela, chave primaria e colunas editaveis. O CRUD
# monta o SQL a partir DESTE dicionario, nunca a partir do que o usuario envia,
# e os valores sempre vao como parametro.
ENTIDADES = {
    "associado": {
        "rotulo": "Associados",
        "tabela": "associado",
        "pk": ["id_associado"],
        "auto": True,
        "colunas": ["matricula", "nome", "tipo_pessoa", "status",
                    "id_associado_indicador"],
        "listagem": """
            SELECT a.id_associado, a.matricula, a.nome, a.tipo_pessoa,
                   a.status, a.id_associado_indicador,
                   (SELECT COUNT(*) FROM propriedade p
                     WHERE p.id_associado = a.id_associado) AS propriedades
              FROM associado a
             ORDER BY a.id_associado
             LIMIT 200
        """,
    },
    "propriedade": {
        "rotulo": "Propriedades",
        "tabela": "propriedade",
        "pk": ["id_propriedade"],
        "auto": True,
        "colunas": ["id_associado", "nome", "registro_rural", "municipio",
                    "area_hectares", "status"],
        "listagem": """
            SELECT p.id_propriedade, p.id_associado, a.nome AS associado,
                   p.nome, p.registro_rural, p.municipio, p.area_hectares,
                   p.status
              FROM propriedade p
              JOIN associado a ON a.id_associado = p.id_associado
             ORDER BY p.id_propriedade
             LIMIT 200
        """,
    },
    "cultura": {
        "rotulo": "Culturas",
        "tabela": "cultura",
        "pk": ["id_cultura"],
        "auto": True,
        "colunas": ["nome", "categoria", "unidade_medida"],
        "listagem": """
            SELECT c.id_cultura, c.nome, c.categoria, c.unidade_medida,
                   (SELECT COUNT(*) FROM lote l
                     WHERE l.id_cultura = c.id_cultura) AS lotes
              FROM cultura c
             ORDER BY c.id_cultura
             LIMIT 200
        """,
    },
    "lote": {
        "rotulo": "Lotes",
        "tabela": "lote",
        "pk": ["id_safra", "numero_lote"],
        "auto": False,
        "colunas": ["id_safra", "numero_lote", "id_propriedade", "id_cultura",
                    "quantidade_planejada", "status"],
        "listagem": """
            SELECT l.id_safra, l.numero_lote, s.descricao AS safra,
                   p.nome AS propriedade, c.nome AS cultura,
                   l.quantidade_planejada, l.status
              FROM lote l
              JOIN safra s       ON s.id_safra = l.id_safra
              JOIN propriedade p ON p.id_propriedade = l.id_propriedade
              JOIN cultura c     ON c.id_cultura = l.id_cultura
             ORDER BY l.id_safra, l.numero_lote
             LIMIT 200
        """,
    },
}


def lista(perfil, entidade):
    cfg = ENTIDADES[entidade]
    return consulta(perfil, cfg["listagem"])


def busca_um(perfil, entidade, chave_valores):
    cfg = ENTIDADES[entidade]
    onde = " AND ".join(f"{c} = %s" for c in cfg["pk"])
    sql = f"SELECT * FROM {cfg['tabela']} WHERE {onde}"
    linhas = consulta(perfil, sql, tuple(chave_valores))
    return linhas[0] if linhas else None


def insere(perfil, entidade, dados):
    """INSERT parametrizado.

    As colunas vem de ENTIDADES (lista fechada no codigo). Os valores vem do
    formulario e viajam como parametro - por isso o %s repetido.
    """
    cfg = ENTIDADES[entidade]
    colunas = [c for c in cfg["colunas"] if c in dados]
    marcadores = ", ".join(["%s"] * len(colunas))
    sql = (f"INSERT INTO {cfg['tabela']} ({', '.join(colunas)}) "
           f"VALUES ({marcadores})")
    valores = tuple(dados[c] for c in colunas)
    return executa(perfil, sql, valores)


def atualiza(perfil, entidade, chave_valores, dados):
    cfg = ENTIDADES[entidade]
    # So entram colunas que constam da definicao da entidade. Um campo extra
    # injetado no formulario e simplesmente ignorado aqui.
    colunas = [c for c in cfg["colunas"] if c in dados and c not in cfg["pk"]]
    if not colunas:
        return 0, None
    atribuicoes = ", ".join(f"{c} = %s" for c in colunas)
    onde = " AND ".join(f"{c} = %s" for c in cfg["pk"])
    sql = f"UPDATE {cfg['tabela']} SET {atribuicoes} WHERE {onde}"
    valores = tuple(dados[c] for c in colunas) + tuple(chave_valores)
    return executa(perfil, sql, valores)


def remove(perfil, entidade, chave_valores):
    cfg = ENTIDADES[entidade]
    onde = " AND ".join(f"{c} = %s" for c in cfg["pk"])
    sql = f"DELETE FROM {cfg['tabela']} WHERE {onde}"
    return executa(perfil, sql, tuple(chave_valores))


# ---------------------------------------------------------------------------
# B1 - Consulta parametrizada 1: producao por cultura e periodo
# ---------------------------------------------------------------------------
SQL_CONSULTA_PRODUCAO = """
    SELECT c.nome                                  AS cultura,
           s.descricao                             AS safra,
           COUNT(DISTINCT l.numero_lote)           AS lotes,
           COUNT(e.id_entrega)                     AS entregas,
           ROUND(SUM(e.quantidade), 2)             AS kg_total,
           ROUND(AVG(e.preco_unitario_kg), 2)      AS preco_medio,
           ROUND(SUM(e.quantidade * e.preco_unitario_kg), 2) AS valor_total
      FROM entrega e
      JOIN lote l    ON l.id_safra = e.id_safra
                    AND l.numero_lote = e.numero_lote
      JOIN cultura c ON c.id_cultura = l.id_cultura
      JOIN safra s   ON s.id_safra = l.id_safra
     WHERE e.data_entrega BETWEEN %s AND %s
       AND e.status = %s
       AND (%s = '' OR c.nome LIKE CONCAT('%', %s, '%'))
     GROUP BY c.nome, s.descricao
    HAVING SUM(e.quantidade) >= %s
     ORDER BY valor_total DESC
     LIMIT 100
"""


def consulta_producao(perfil, data_ini, data_fim, status, cultura, kg_minimo):
    """Junção de 4 tabelas com agregacao, HAVING e filtros do usuario.

    Os cinco filtros digitados pelo usuario viajam como parametro. Note o
    truque do terceiro filtro: em vez de montar a clausula so quando o campo
    esta preenchido - o que exigiria concatenar SQL -, o proprio comando trata
    o campo vazio com (%s = '' OR ...). O SQL e sempre o mesmo texto.
    """
    return consulta(perfil, SQL_CONSULTA_PRODUCAO,
                    (data_ini, data_fim, status, cultura, cultura, kg_minimo))


# ---------------------------------------------------------------------------
# B1 - Consulta parametrizada 2: desempenho por associado
# ---------------------------------------------------------------------------
SQL_CONSULTA_ASSOCIADOS = """
    SELECT a.matricula,
           a.nome                                   AS associado,
           a.tipo_pessoa,
           a.status,
           COUNT(DISTINCT p.id_propriedade)         AS propriedades,
           ROUND(SUM(p.area_hectares), 2)           AS area_total,
           COUNT(DISTINCT CONCAT(l.id_safra,'-',l.numero_lote)) AS lotes,
           COALESCE(COUNT(e.id_entrega), 0)         AS entregas,
           ROUND(COALESCE(SUM(e.quantidade), 0), 2) AS kg_entregues
      FROM associado a
      LEFT JOIN propriedade p ON p.id_associado = a.id_associado
      LEFT JOIN lote l        ON l.id_propriedade = p.id_propriedade
      LEFT JOIN entrega e     ON e.id_safra = l.id_safra
                             AND e.numero_lote = l.numero_lote
                             AND e.status = 'RECEBIDA'
     WHERE (%s = '' OR a.nome LIKE CONCAT('%', %s, '%'))
       AND (%s = '' OR a.status = %s)
       AND (%s = '' OR a.tipo_pessoa = %s)
     GROUP BY a.id_associado, a.matricula, a.nome, a.tipo_pessoa, a.status
    HAVING area_total >= %s OR area_total IS NULL
     ORDER BY kg_entregues DESC
     LIMIT 100
"""


def consulta_associados(perfil, nome, status, tipo, area_minima):
    return consulta(perfil, SQL_CONSULTA_ASSOCIADOS,
                    (nome, nome, status, status, tipo, tipo, area_minima))


# ---------------------------------------------------------------------------
# B1 - Relatorio consolidado alimentado por VISAO
# ---------------------------------------------------------------------------
def relatorio_safra(perfil, id_safra):
    """Le a visao vw_relatorio_safra_associado.

    A aplicacao nao conhece as junçoes do relatorio: elas moram na visao,
    definida em sql/04_views.sql. Isso mantem a regra de consolidacao no banco,
    onde ela pode ser reusada por outras ferramentas.
    """
    sql = """
        SELECT * FROM vw_relatorio_safra_associado
         WHERE (%s = 0 OR id_safra = %s)
         ORDER BY safra, associado
         LIMIT 300
    """
    return consulta(perfil, sql, (id_safra, id_safra))


def lista_safras(perfil):
    return consulta(perfil,
                    "SELECT id_safra, descricao, status FROM safra "
                    "ORDER BY id_safra LIMIT 200")


# ---------------------------------------------------------------------------
# B1/B3 - OPERACAO TRANSACIONAL MULTITABELA
# ---------------------------------------------------------------------------
def fecha_prestacao_contas(perfil, id_associado, id_safra, percentual_desconto,
                           forcar_erro=False):
    """Fecha a prestacao de contas de um associado numa safra.

    Esta e a operacao central do B1: uma unica transacao que altera DUAS
    tabelas - prestacao_contas e movimento_financeiro.

    Passos dentro da transacao:
      1. apura o bruto a partir das entregas RECEBIDAS do associado na safra;
      2. calcula o desconto (taxa da cooperativa) e o saldo;
      3. grava ou atualiza a linha em prestacao_contas;
      4. lanca o movimento financeiro de credito correspondente ao saldo;
      5. marca a prestacao como FECHADA.

    Por que precisa ser atomico: se o passo 4 falhar depois do passo 3, a
    cooperativa teria uma prestacao fechada sem o lancamento financeiro que a
    paga - o associado apareceria como quitado sem ter recebido. Os dois
    comandos descrevem um unico fato do negocio e tem que valer juntos ou
    nenhum.

    forcar_erro: usado na demonstracao do B3. Injeta um desconto maior que o
    bruto no meio da transacao, violando ck_prestacao_descontos DEPOIS que a
    primeira tabela ja foi escrita, para evidenciar o ROLLBACK.
    """
    passos = []
    with conexao(perfil) as con:
        cur = con.cursor(dictionary=True, prepared=True)
        try:
            con.start_transaction()
            passos.append("START TRANSACTION")

            # 1. apuracao
            cur.execute("""
                SELECT ROUND(COALESCE(SUM(e.quantidade * e.preco_unitario_kg), 0), 2) AS bruto,
                       COUNT(e.id_entrega) AS entregas
                  FROM entrega e
                  JOIN lote l        ON l.id_safra = e.id_safra
                                    AND l.numero_lote = e.numero_lote
                  JOIN propriedade p ON p.id_propriedade = l.id_propriedade
                 WHERE p.id_associado = %s
                   AND l.id_safra = %s
                   AND e.status = 'RECEBIDA'
            """, (id_associado, id_safra))
            apuracao = cur.fetchone()
            bruto = dinheiro(apuracao["bruto"] or 0)
            passos.append(
                f"SELECT apuracao -> bruto = {bruto} "
                f"({apuracao['entregas']} entregas recebidas)")

            if bruto <= 0:
                raise ValueError(
                    "Esse associado nao tem entregas recebidas nesta safra, "
                    "entao nao ha o que fechar.")

            desconto = dinheiro(bruto * dinheiro(percentual_desconto) / 100)
            if forcar_erro:
                # Violacao deliberada: desconto maior que o bruto fere
                # ck_prestacao_descontos. Repare que a violacao so acontece no
                # comando da PRIMEIRA tabela, depois que a transacao ja esta
                # aberta - e esse o ponto da demonstracao.
                desconto = dinheiro(bruto * Decimal("1.5"))
                passos.append(
                    f"FALHA INJETADA: desconto forcado para {desconto}, "
                    f"maior que o bruto {bruto}")
            saldo = dinheiro(bruto - desconto)

            # 2. prestacao_contas (TABELA 1)
            cur.execute("""
                INSERT INTO prestacao_contas
                       (id_associado, id_safra, total_bruto, total_descontos,
                        saldo, status)
                VALUES (%s, %s, %s, %s, %s, 'ABERTA')
                ON DUPLICATE KEY UPDATE
                       total_bruto     = VALUES(total_bruto),
                       total_descontos = VALUES(total_descontos),
                       saldo           = VALUES(saldo),
                       status          = 'ABERTA'
            """, (id_associado, id_safra, bruto, desconto, saldo))
            passos.append(
                f"INSERT/UPDATE prestacao_contas -> bruto {bruto:.2f}, "
                f"desconto {desconto:.2f}, saldo {saldo:.2f}")

            cur.execute("""
                SELECT id_prestacao FROM prestacao_contas
                 WHERE id_associado = %s AND id_safra = %s
            """, (id_associado, id_safra))
            id_prestacao = cur.fetchone()["id_prestacao"]

            # 3. movimento_financeiro (TABELA 2)
            referencia = f"CRED-{id_prestacao}-{id_safra}-{id_associado}"
            # ON DUPLICATE KEY UPDATE em vez de DELETE + INSERT: o perfil
            # financeiro nao tem (e nao deve ter) DELETE em movimento
            # financeiro, porque lancamento contabil nao se apaga, se corrige.
            # A chave de conflito e uq_movimento_referencia.
            cur.execute("""
                INSERT INTO movimento_financeiro
                       (id_prestacao, data_movimento, valor, tipo, status,
                        referencia)
                VALUES (%s, CURDATE(), %s, 'CREDITO', 'LIQUIDADO', %s)
                ON DUPLICATE KEY UPDATE
                       valor          = VALUES(valor),
                       data_movimento = CURDATE(),
                       status         = 'LIQUIDADO'
            """, (id_prestacao, saldo, referencia))
            passos.append(
                f"INSERT movimento_financeiro -> CREDITO {saldo:.2f} "
                f"(referencia {referencia})")

            # 4. fechamento
            cur.execute("""
                UPDATE prestacao_contas SET status = 'FECHADA'
                 WHERE id_prestacao = %s
            """, (id_prestacao,))
            passos.append("UPDATE prestacao_contas -> status = FECHADA")

            con.commit()
            passos.append("COMMIT")
            return True, passos, {
                "id_prestacao": id_prestacao, "bruto": bruto,
                "desconto": desconto, "saldo": saldo,
            }

        except Exception as erro:
            con.rollback()
            passos.append("ROLLBACK")
            if isinstance(erro, ValueError):
                passos.append(f"motivo: {erro}")
                return False, passos, {"mensagem": str(erro)}
            mensagem = traduz_erro(erro)
            passos.append(f"motivo: {mensagem}")
            return False, passos, {"mensagem": mensagem}
        finally:
            cur.close()


def estado_prestacao(perfil, id_associado, id_safra):
    """Fotografia das duas tabelas da transacao, para provar integridade."""
    sql = """
        SELECT pc.id_prestacao, pc.total_bruto, pc.total_descontos, pc.saldo,
               pc.status,
               (SELECT COUNT(*) FROM movimento_financeiro m
                 WHERE m.id_prestacao = pc.id_prestacao) AS movimentos,
               (SELECT COALESCE(SUM(m.valor), 0) FROM movimento_financeiro m
                 WHERE m.id_prestacao = pc.id_prestacao
                   AND m.tipo = 'CREDITO') AS total_creditos
          FROM prestacao_contas pc
         WHERE pc.id_associado = %s AND pc.id_safra = %s
    """
    linhas = consulta(perfil, sql, (id_associado, id_safra))
    return linhas[0] if linhas else None


def auditoria_recente(perfil, limite=30):
    return consulta(perfil, """
        SELECT tabela, operacao, chave_registro, campo,
               valor_anterior, valor_novo, usuario, data_hora
          FROM auditoria
         ORDER BY id_auditoria DESC
         LIMIT %s
    """, (limite,))
