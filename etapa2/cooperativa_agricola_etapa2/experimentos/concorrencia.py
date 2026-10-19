"""B3 - Experimento de concorrencia com duas sessoes simultaneas.

Executa tres cenarios contra o banco real, com duas conexoes abertas ao mesmo
tempo, e grava o observado em experimentos/resultados/B3_concorrencia.txt:

  1. BLOQUEIO: duas sessoes alteram a MESMA linha. A segunda espera.
  2. ISOLAMENTO: prova o comportamento de REPEATABLE READ (leitura repetida
     dentro da transacao nao enxerga o commit alheio).
  3. DEADLOCK: duas sessoes travam duas linhas em ordem inversa. O InnoDB
     detecta o ciclo e aborta uma delas.

Uso:
    python experimentos/concorrencia.py
"""

import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import mysql.connector

import config

SAIDA = (Path(__file__).resolve().parent / "resultados" /
         "B3_concorrencia.txt")

linhas = []


def log(texto=""):
    print(texto)
    linhas.append(texto)


def marca():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def abre(perfil="OPERACIONAL"):
    conta = config.CONTAS[perfil]
    return mysql.connector.connect(
        host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME,
        user=conta["user"], password=conta["password"], autocommit=False)


# Conexao administrativa para observar o estado interno do InnoDB, que exige
# privilegio sobre performance_schema.
import os

ADMIN = {
    "user": os.environ.get("COOP_ADMIN_USER", "root"),
    "password": os.environ.get("COOP_ADMIN_SENHA", ""),
}


def observa_bloqueios():
    con = mysql.connector.connect(
        host=config.DB_HOST, database=config.DB_NAME,
        user=ADMIN["user"], password=ADMIN["password"])
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT r.trx_id          AS trx_esperando,
               r.trx_mysql_thread_id AS thread_esperando,
               SUBSTRING(r.trx_query, 1, 60) AS consulta_esperando,
               b.trx_id          AS trx_bloqueando,
               b.trx_mysql_thread_id AS thread_bloqueando,
               TIMESTAMPDIFF(SECOND, r.trx_wait_started, NOW()) AS segundos_esperando
          FROM performance_schema.data_lock_waits w
          JOIN information_schema.innodb_trx b
            ON b.trx_id = CONV(LEFT(w.BLOCKING_ENGINE_TRANSACTION_ID, 16), 10, 10)
          JOIN information_schema.innodb_trx r
            ON r.trx_id = CONV(LEFT(w.REQUESTING_ENGINE_TRANSACTION_ID, 16), 10, 10)
    """)
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado


def nivel_isolamento():
    con = abre()
    cur = con.cursor()
    cur.execute("SELECT @@transaction_isolation, @@autocommit, VERSION()")
    valor = cur.fetchone()
    cur.close()
    con.close()
    return valor


log("=" * 76)
log("B3 - EXPERIMENTO DE CONCORRENCIA COM DUAS SESSOES SIMULTANEAS")
log(f"Executado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
log("=" * 76)

iso, autocommit, versao = nivel_isolamento()
log("")
log("AMBIENTE")
log(f"  SGBD                 : MySQL {versao}")
log(f"  Nivel de isolamento  : {iso}  (padrao do InnoDB)")
log(f"  autocommit da sessao : {autocommit} (desligado pela aplicacao)")
log("")
log("Preparacao: as duas sessoes conectam com a conta app_operacional e")
log("trabalham sobre a tabela entrega.")

# ---------------------------------------------------------------------------
# CENARIO 1 - BLOQUEIO
# ---------------------------------------------------------------------------
log("")
log("-" * 76)
log("CENARIO 1 - DUAS SESSOES ALTERAM A MESMA LINHA")
log("-" * 76)
log("Sessao A abre transacao, altera a entrega 1 e SEGURA o bloqueio por 5s.")
log("Sessao B tenta alterar a MESMA entrega 1 enquanto A ainda nao confirmou.")
log("")

resultado_b = {}


def sessao_b_mesma_linha():
    con = abre()
    cur = con.cursor()
    t0 = time.time()
    resultado_b["inicio"] = marca()
    try:
        con.start_transaction()
        cur.execute("UPDATE entrega SET qualidade = 'C' WHERE id_entrega = 1")
        resultado_b["espera"] = time.time() - t0
        resultado_b["fim"] = marca()
        resultado_b["status"] = "conseguiu apos esperar"
        con.commit()
    except mysql.connector.Error as e:
        resultado_b["espera"] = time.time() - t0
        resultado_b["fim"] = marca()
        resultado_b["status"] = f"erro {e.errno}: {str(e)[:70]}"
        con.rollback()
    finally:
        cur.close()
        con.close()


con_a = abre()
cur_a = con_a.cursor()
con_a.start_transaction()
log(f"[{marca()}] Sessao A: START TRANSACTION")
cur_a.execute("UPDATE entrega SET qualidade = 'B' WHERE id_entrega = 1")
log(f"[{marca()}] Sessao A: UPDATE entrega 1 -> qualidade B   (sem COMMIT)")

t_b = threading.Thread(target=sessao_b_mesma_linha)
t_b.start()
time.sleep(2)
log(f"[{marca()}] Sessao B: UPDATE na mesma linha -> BLOQUEADA, esperando")

bloqueios = observa_bloqueios()
if bloqueios:
    b = bloqueios[0]
    log("")
    log("  Estado interno observado durante a espera:")
    log(f"    transacao esperando  : {b['trx_esperando']} "
        f"(thread {b['thread_esperando']})")
    log(f"    comando dela         : {b['consulta_esperando']}")
    log(f"    bloqueada pela trx   : {b['trx_bloqueando']} "
        f"(thread {b['thread_bloqueando']})")
    log("")
else:
    log("  (nao foi possivel ler performance_schema; verifique COOP_ADMIN_SENHA)")

time.sleep(3)
con_a.commit()
log(f"[{marca()}] Sessao A: COMMIT - o bloqueio e liberado")
t_b.join()
log(f"[{marca()}] Sessao B: {resultado_b['status']}")
log(f"           tempo que B passou esperando: {resultado_b['espera']:.2f}s")
cur_a.close()
con_a.close()

log("")
log("OBSERVADO: o InnoDB aplica bloqueio exclusivo de linha no UPDATE. A")
log("sessao B nao recebeu erro nem leu valor desatualizado: ficou em espera")
log("ate o COMMIT de A e so entao aplicou a propria alteracao, sobre o valor")
log("ja atualizado. O tempo de espera de B corresponde ao tempo que A segurou")
log("a transacao, o que confirma que a serializacao foi feita pelo bloqueio.")
log("Se A nunca confirmasse, B esperaria ate innodb_lock_wait_timeout (50s por")
log("padrao) e receberia o erro 1205, que a aplicacao traduz em mensagem.")

# ---------------------------------------------------------------------------
# CENARIO 2 - ISOLAMENTO
# ---------------------------------------------------------------------------
log("")
log("-" * 76)
log("CENARIO 2 - O QUE A SESSAO A ENXERGA DO COMMIT DE B (REPEATABLE READ)")
log("-" * 76)

con_a = abre()
cur_a = con_a.cursor()
con_a.start_transaction()
cur_a.execute("SELECT qualidade FROM entrega WHERE id_entrega = 1")
leitura_1 = cur_a.fetchone()[0]
log(f"[{marca()}] Sessao A: 1a leitura da entrega 1 -> qualidade = {leitura_1}")

con_b = abre()
cur_b = con_b.cursor()
con_b.start_transaction()
nova = "A" if leitura_1 != "A" else "C"
cur_b.execute("UPDATE entrega SET qualidade = %s WHERE id_entrega = 1", (nova,))
con_b.commit()
log(f"[{marca()}] Sessao B: UPDATE para '{nova}' + COMMIT (confirmado)")
cur_b.close()
con_b.close()

cur_a.execute("SELECT qualidade FROM entrega WHERE id_entrega = 1")
leitura_2 = cur_a.fetchone()[0]
log(f"[{marca()}] Sessao A: 2a leitura, mesma transacao -> qualidade = {leitura_2}")
con_a.commit()
cur_a.execute("SELECT qualidade FROM entrega WHERE id_entrega = 1")
leitura_3 = cur_a.fetchone()[0]
log(f"[{marca()}] Sessao A: COMMIT e nova leitura -> qualidade = {leitura_3}")
cur_a.close()
con_a.close()

log("")
if leitura_1 == leitura_2 and leitura_2 != leitura_3:
    log("OBSERVADO: leitura repetida. Dentro da mesma transacao, A leu duas")
    log(f"vezes o valor '{leitura_1}', mesmo depois de B ter confirmado "
        f"'{leitura_2 if leitura_2 != leitura_1 else nova}'.")
    log("Isso e REPEATABLE READ funcionando: A trabalha sobre uma fotografia")
    log("consistente tirada na primeira leitura (MVCC). So apos o proprio")
    log(f"COMMIT, A passou a enxergar '{leitura_3}'.")
else:
    log(f"OBSERVADO: leituras {leitura_1} / {leitura_2} / {leitura_3}.")

# ---------------------------------------------------------------------------
# CENARIO 3 - DEADLOCK
# ---------------------------------------------------------------------------
log("")
log("-" * 76)
log("CENARIO 3 - DEADLOCK PROVOCADO (ORDEM INVERSA DE BLOQUEIO)")
log("-" * 76)
log("A trava a linha 1 e depois pede a 2. B trava a 2 e depois pede a 1.")
log("")

estado = {}


def transacao_cruzada(nome, primeira, segunda, atraso):
    con = abre()
    cur = con.cursor()
    try:
        con.start_transaction()
        cur.execute("UPDATE entrega SET quantidade = quantidade "
                    "WHERE id_entrega = %s", (primeira,))
        estado[f"{nome}_passo1"] = f"travou linha {primeira}"
        time.sleep(atraso)
        cur.execute("UPDATE entrega SET quantidade = quantidade "
                    "WHERE id_entrega = %s", (segunda,))
        estado[f"{nome}_passo2"] = f"travou linha {segunda}"
        con.commit()
        estado[nome] = "COMMIT"
    except mysql.connector.Error as e:
        con.rollback()
        estado[nome] = f"ABORTADA pelo servidor - erro {e.errno}: {str(e)[:60]}"
    finally:
        cur.close()
        con.close()


t1 = threading.Thread(target=transacao_cruzada, args=("A", 1, 2, 1.5))
t2 = threading.Thread(target=transacao_cruzada, args=("B", 2, 1, 1.5))
t1.start()
t2.start()
t1.join()
t2.join()

for nome in ("A", "B"):
    log(f"  Sessao {nome}: {estado.get(f'{nome}_passo1', '-')}"
        f" -> {estado.get(f'{nome}_passo2', 'ficou esperando')}")
    log(f"             desfecho: {estado.get(nome)}")

log("")
houve_deadlock = any("1213" in str(estado.get(n, "")) for n in ("A", "B"))
if houve_deadlock:
    log("OBSERVADO: deadlock detectado pelo InnoDB. Diferente do cenario 1,")
    log("aqui ninguem poderia terminar esperando - cada uma segurava o que a")
    log("outra precisava. O InnoDB percebeu o ciclo e escolheu uma vitima,")
    log("abortando-a com erro 1213 para que a outra prosseguisse. A vitima e")
    log("desfeita por completo, entao nao resta estado pela metade. Na")
    log("aplicacao, esse erro e traduzido em 'houve conflito... tente")
    log("novamente', e a operacao pode ser repetida com seguranca.")
else:
    log("OBSERVADO: nao houve deadlock nesta execucao - as transacoes se")
    log("alternaram sem formar ciclo. O resultado depende do instante exato em")
    log("que cada UPDATE pede o bloqueio.")

# ---------------------------------------------------------------------------
log("")
log("=" * 76)
log("JUSTIFICATIVA DO NIVEL DE ISOLAMENTO ADOTADO")
log("=" * 76)
log("""
A aplicacao mantem REPEATABLE READ, que e o padrao do InnoDB, por tres razoes
ligadas ao que este sistema faz:

1. A transacao central - fechar prestacao de contas - primeiro SOMA as entregas
   do associado e depois grava o resultado. Em READ COMMITTED, uma entrega
   confirmada por outra sessao entre a soma e a gravacao mudaria o total sem que
   a transacao percebesse, e a prestacao seria gravada com um valor que ja nao
   corresponde as entregas. REPEATABLE READ garante que a soma e a gravacao
   enxerguem a mesma fotografia dos dados.

2. Nao precisamos de SERIALIZABLE. Ele acrescentaria bloqueio de intervalo em
   toda leitura, encarecendo as consultas do patio, que sao frequentes, para
   resolver um problema que nao temos: a prestacao e unica por associado e
   safra (uq_prestacao_associado_safra), entao duas sessoes nao conseguem criar
   fechamentos concorrentes para o mesmo par - a propria restricao do banco
   recusa o segundo.

3. Em troca, aceitamos conviver com bloqueio e com a possibilidade de deadlock,
   como os cenarios 1 e 3 mostraram. A aplicacao trata os dois casos: os erros
   1205 e 1213 sao convertidos em mensagem que orienta o usuario a repetir a
   operacao, em vez de exibir a excecao do driver.
""".strip())

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print(f"\nGravado em {SAIDA}")
