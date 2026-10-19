"""B5 - Teste dos tres perfis de acesso com login real.

Cada teste abre uma conexao com a conta de banco do perfil e executa um
comando, confirmando que o SGBD permite o que deve permitir e recusa o que
deve recusar. O que se verifica aqui e o GRANT, nao a aplicacao: mesmo que a
interface tivesse uma falha de autorizacao, estes limites continuariam valendo.

Uso:
    python experimentos/teste_perfis.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import mysql.connector

import config

SAIDA = (Path(__file__).resolve().parent / "resultados" /
         "B5_teste_perfis.txt")

linhas = []
divergencias = 0


def log(t=""):
    print(t)
    linhas.append(t)


def testa(perfil, rotulo, esperado, sql):
    global divergencias
    conta = config.CONTAS[perfil]
    retorno = ""
    try:
        con = mysql.connector.connect(
            host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME,
            user=conta["user"], password=conta["password"], autocommit=True)
        cur = con.cursor()
        cur.execute(sql)
        try:
            resultado = cur.fetchall()
            retorno = f"{len(resultado)} linha(s): {resultado[:3]}"
        except mysql.connector.Error:
            retorno = f"{cur.rowcount} linha(s) afetada(s)"
        cur.close()
        con.close()
        obtido = "PERMITIDO"
    except mysql.connector.Error as e:
        obtido = "NEGADO"
        retorno = f"erro {e.errno}: {str(e)[:90]}"

    veredito = "confere" if obtido == esperado else "DIVERGE"
    if veredito == "DIVERGE":
        divergencias += 1
    log(f"[{perfil}] {rotulo}")
    log(f"  SQL      : {sql}")
    log(f"  esperado : {esperado} | obtido: {obtido} | {veredito}")
    log(f"  retorno  : {retorno}")
    log("")


log("=" * 76)
log("B5 - TESTE DOS TRES PERFIS DE ACESSO COM LOGIN REAL")
log(f"Banco: cooperativa_agricola | MySQL 8.0 | "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")
log("=" * 76)
log("")

log("--- PERFIL 1: LEITURA (papel coop_leitura) ---")
testa("LEITURA", "Consulta a visao com documento mascarado", "PERMITIDO",
      "SELECT id_associado, nome, documento_mascarado "
      "FROM vw_associado_publico LIMIT 3")
testa("LEITURA", "Tenta ler o CPF real na tabela base", "NEGADO",
      "SELECT cpf FROM associado_pf LIMIT 1")
testa("LEITURA", "Tenta ler prestacao de contas por linha", "NEGADO",
      "SELECT * FROM prestacao_contas LIMIT 1")
testa("LEITURA", "Le o mesmo dado financeiro pela visao consolidada",
      "PERMITIDO",
      "SELECT associado, saldo FROM vw_relatorio_safra_associado "
      "WHERE saldo IS NOT NULL LIMIT 3")
testa("LEITURA", "Tenta inserir uma entrega", "NEGADO",
      "INSERT INTO entrega (id_safra,numero_lote,data_entrega,quantidade,"
      "qualidade,preco_unitario_kg,status) "
      "VALUES (1,1,'2024-01-01',10,'A',1,'PENDENTE')")

log("--- PERFIL 2: OPERACIONAL (papel coop_operacional) ---")
testa("OPERACIONAL", "Consulta lotes", "PERMITIDO",
      "SELECT id_safra, numero_lote, status FROM lote LIMIT 3")
testa("OPERACIONAL", "Tenta ler prestacao de contas", "NEGADO",
      "SELECT * FROM prestacao_contas LIMIT 1")
testa("OPERACIONAL", "Tenta apagar entrega (estorno deve ser por status)",
      "NEGADO", "DELETE FROM entrega WHERE id_entrega = 999999")

log("--- PERFIL 3: FINANCEIRO (papel coop_financeiro) ---")
testa("FINANCEIRO", "Consulta prestacao de contas", "PERMITIDO",
      "SELECT id_prestacao, saldo, status FROM prestacao_contas LIMIT 3")
testa("FINANCEIRO", "Tenta alterar preco de entrega (privilegio revogado)",
      "NEGADO", "UPDATE entrega SET preco_unitario_kg = 99 WHERE id_entrega = 1")
testa("FINANCEIRO", "Tenta alterar cadastro de associado", "NEGADO",
      "UPDATE associado SET nome = 'alterado' WHERE id_associado = 1")

log("=" * 76)
log(f"RESULTADO: {divergencias} divergencia(s) em 11 testes")
log("=" * 76)
log("")
log("Observacao sobre o perfil de leitura: ele le o saldo pela visao")
log("vw_relatorio_safra_associado sem ter SELECT em prestacao_contas. Isso")
log("funciona porque a visao do MySQL e, por padrao, SQL SECURITY DEFINER -")
log("executa com o privilegio de quem a criou. E esse mecanismo que permite")
log("liberar o agregado sem liberar a linha.")

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print(f"\nGravado em {SAIDA}")
sys.exit(1 if divergencias else 0)
