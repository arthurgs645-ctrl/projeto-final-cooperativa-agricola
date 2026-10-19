"""B2 - Demonstracao de resistencia a injecao de SQL.

Compara, lado a lado e contra o banco real, o que acontece com a MESMA entrada
maliciosa em duas implementacoes:

  (A) VULNERAVEL  - SQL montado por concatenacao de string.
  (B) SEGURA      - a que a aplicacao usa: consulta parametrizada.

A versao vulneravel existe apenas neste arquivo de demonstracao e nao e usada
em lugar nenhum da aplicacao. Ela esta aqui para que a diferenca seja medida,
e nao apenas afirmada.

Uso:
    python experimentos/injecao_sql.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import mysql.connector

import config

SAIDA = (Path(__file__).resolve().parent / "resultados" /
         "B2_injecao_sql.txt")

linhas = []


def log(t=""):
    print(t)
    linhas.append(t)


def abre():
    conta = config.CONTAS["LEITURA"]
    return mysql.connector.connect(
        host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME,
        user=conta["user"], password=conta["password"])


def versao_vulneravel(entrada):
    """NAO USAR. Concatena a entrada no texto do comando."""
    sql = ("SELECT id_associado, nome, matricula FROM associado "
           f"WHERE nome = '{entrada}'")
    con = abre()
    cur = con.cursor()
    try:
        cur.execute(sql)
        linhas_ = cur.fetchall()
        return sql, linhas_, None
    except mysql.connector.Error as e:
        return sql, [], f"erro {e.errno}: {str(e)[:80]}"
    finally:
        cur.close()
        con.close()


def versao_segura(entrada):
    """A que a aplicacao usa: o valor viaja como parametro."""
    sql = ("SELECT id_associado, nome, matricula FROM associado "
           "WHERE nome = %s")
    con = abre()
    cur = con.cursor(prepared=True)
    try:
        cur.execute(sql, (entrada,))
        linhas_ = cur.fetchall()
        return sql, linhas_, None
    except mysql.connector.Error as e:
        return sql, [], f"erro {e.errno}: {str(e)[:80]}"
    finally:
        cur.close()
        con.close()


ATAQUES = [
    ("' OR '1'='1",
     "Tautologia: fecha a aspa e acrescenta uma condicao sempre verdadeira, "
     "tentando devolver a tabela inteira."),
    ("' UNION SELECT 1, cpf, 1 FROM associado_pf -- ",
     "UNION: tenta anexar um segundo SELECT para extrair CPF, que este perfil "
     "nao pode ler."),
    ("Ana Cardoso' --",
     "Comentario: tenta truncar o restante do comando."),
]

log("=" * 76)
log("B2 - TENTATIVA DE INJECAO DE SQL: VULNERAVEL x PARAMETRIZADA")
log(f"Executado em {datetime.now().strftime('%d/%m/%Y %H:%M')} contra o banco real")
log("=" * 76)
log("")
log("Consulta de referencia: busca de associado por nome exato.")
log("A entrada abaixo e o que um usuario digitaria no campo 'nome'.")

# linha de controle: uma busca legitima, para mostrar que as duas versoes
# funcionam igual quando a entrada e honesta
log("")
log("-" * 76)
log("CONTROLE - entrada legitima: Ana Cardoso")
log("-" * 76)
_, r_vul, _ = versao_vulneravel("Ana Cardoso")
_, r_seg, _ = versao_segura("Ana Cardoso")
log(f"  versao vulneravel  : {len(r_vul)} linha(s) -> {r_vul}")
log(f"  versao parametrizada: {len(r_seg)} linha(s) -> {r_seg}")
log("  As duas se comportam igual com entrada honesta.")

total_associados = None
con = abre()
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM associado")
total_associados = cur.fetchone()[0]
cur.close()
con.close()
log(f"\n  (a tabela associado tem {total_associados} linhas no total)")

for entrada, explicacao in ATAQUES:
    log("")
    log("-" * 76)
    log(f"ATAQUE: {entrada}")
    log("-" * 76)
    log(f"  {explicacao}")
    log("")

    sql_v, linhas_v, erro_v = versao_vulneravel(entrada)
    log("  (A) VERSAO VULNERAVEL - concatenacao")
    log(f"      SQL que chegou ao banco:")
    log(f"        {sql_v}")
    if erro_v:
        log(f"      resultado: {erro_v}")
        log("      -> o comando quebrou, o que ja revela estrutura interna ao atacante")
    else:
        log(f"      resultado: {len(linhas_v)} linha(s) devolvida(s)")
        if len(linhas_v) >= total_associados:
            log("      -> VAZAMENTO: devolveu a tabela inteira")
        elif linhas_v:
            log(f"      -> VAZAMENTO: {linhas_v[:3]}")

    sql_s, linhas_s, erro_s = versao_segura(entrada)
    log("")
    log("  (B) VERSAO PARAMETRIZADA - a que a aplicacao usa")
    log(f"      SQL que chegou ao banco:")
    log(f"        {sql_s}")
    log(f"      parametro enviado separadamente: {entrada!r}")
    if erro_s:
        log(f"      resultado: {erro_s}")
    else:
        log(f"      resultado: {len(linhas_s)} linha(s) devolvida(s)")
        log("      -> o texto foi tratado como um NOME a procurar, nao como comando")

log("")
log("=" * 76)
log("CONCLUSAO")
log("=" * 76)
log("""
A diferenca nao esta em filtrar ou escapar caracteres, e sim em COMO o comando
chega ao servidor. Na versao parametrizada, o texto do SQL e enviado e
compilado uma vez, com marcadores no lugar dos valores; os valores viajam
depois, por um canal separado do protocolo. Quando o servidor recebe
"' OR '1'='1", ele ja terminou de decidir o que o comando faz - aquele texto so
pode ser conteudo do parametro, jamais sintaxe.

Por isso a aplicacao nao tenta remover aspas nem palavras como DROP: essa
abordagem (lista de bloqueio) falha sempre que alguem encontra uma codificacao
nao prevista. Parametrizar elimina a classe inteira do problema.

Alem da parametrizacao, a aplicacao ganha uma segunda barreira do proprio
banco: mesmo que uma injecao passasse, a conta app_leitura nao tem privilegio
de SELECT em associado_pf, entao o UNION acima nao conseguiria ler CPF de
qualquer forma. Menor privilegio e parametrizacao se reforcam.
""".strip())

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print(f"\nGravado em {SAIDA}")
