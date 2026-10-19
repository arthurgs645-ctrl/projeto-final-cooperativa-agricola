"""Aplicacao web da Cooperativa Agricola - Etapa 2.

B1 - Aplicacao com interface.

A interface e proposital e deliberadamente simples: o que esta sendo avaliado
e o que ela revela sobre o banco (transacao, consulta parametrizada, tratamento
de erro de restricao, perfil de acesso), nao o visual.

Execucao:
    python app/app.py
    http://127.0.0.1:5000
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)

import auth
import config
import db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ---------------------------------------------------------------------------
# Sessao e perfis
# ---------------------------------------------------------------------------
def usuario_atual():
    return session.get("usuario")


def perfil_atual():
    u = usuario_atual()
    return u["perfil"] if u else None


def exige_login():
    if not usuario_atual():
        flash("Entre com um usuario para continuar.", "aviso")
        return redirect(url_for("login"))
    return None


def exige_perfil(*perfis):
    """Primeira linha de defesa: a aplicacao esconde o que o perfil nao usa.

    A segunda linha e o proprio GRANT no banco: mesmo que esta checagem
    falhasse, a conta MySQL do perfil nao teria privilegio para a operacao.
    """
    if perfil_atual() not in perfis:
        flash("Seu perfil nao tem acesso a essa tela.", "erro")
        return redirect(url_for("inicio"))
    return None


@app.context_processor
def injeta_contexto():
    return {"usuario": usuario_atual(), "entidades": db.ENTIDADES}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_digitado = request.form.get("login", "")
        senha_digitada = request.form.get("senha", "")

        # Consulta parametrizada tambem aqui: a tela de login e o alvo
        # classico de injecao de SQL.
        linhas = db.consulta("LEITURA", """
            SELECT id_usuario, login, nome, perfil, senha_hash, senha_sal,
                   algoritmo, ativo
              FROM usuario_app
             WHERE login = %s
        """, (login_digitado,))

        usuario = linhas[0] if linhas else None
        senha_ok = False
        if usuario:
            senha_ok = auth.confere(senha_digitada, usuario["senha_hash"],
                                    usuario["senha_sal"], usuario["algoritmo"])

        # Mensagem unica para login inexistente e senha errada: dizer qual dos
        # dois falhou entregaria a um atacante a lista de logins validos.
        if not usuario or not senha_ok or not usuario["ativo"]:
            flash("Login ou senha invalidos.", "erro")
            return render_template("login.html")

        session["usuario"] = {
            "id": usuario["id_usuario"],
            "login": usuario["login"],
            "nome": usuario["nome"],
            "perfil": usuario["perfil"],
        }
        return redirect(url_for("inicio"))

    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
@app.route("/")
def inicio():
    r = exige_login()
    if r:
        return r
    return render_template("inicio.html")


# ---------------------------------------------------------------------------
# CRUD - quatro entidades (associado, propriedade, cultura, lote)
# ---------------------------------------------------------------------------
@app.route("/cadastro/<entidade>")
def cadastro_listar(entidade):
    r = exige_login()
    if r:
        return r
    if entidade not in db.ENTIDADES:
        flash("Cadastro desconhecido.", "erro")
        return redirect(url_for("inicio"))
    try:
        linhas = db.lista(perfil_atual(), entidade)
    except Exception as erro:
        flash(db.traduz_erro(erro), "erro")
        linhas = []
    return render_template("cadastro_lista.html", entidade=entidade,
                           cfg=db.ENTIDADES[entidade], linhas=linhas)


@app.route("/cadastro/<entidade>/novo", methods=["GET", "POST"])
def cadastro_novo(entidade):
    r = exige_login() or exige_perfil("OPERACIONAL")
    if r:
        return r
    cfg = db.ENTIDADES[entidade]
    if request.method == "POST":
        dados = _coleta_form(cfg)
        try:
            db.insere(perfil_atual(), entidade, dados)
            flash(f"{cfg['rotulo'][:-1]} cadastrado com sucesso.", "ok")
            return redirect(url_for("cadastro_listar", entidade=entidade))
        except Exception as erro:
            # Aqui esta o requisito de tratamento de erro: o usuario ve a
            # frase traduzida, nunca a excecao do driver.
            flash(db.traduz_erro(erro), "erro")
            return render_template("cadastro_form.html", entidade=entidade,
                                   cfg=cfg, registro=dados, novo=True)
    return render_template("cadastro_form.html", entidade=entidade, cfg=cfg,
                           registro={}, novo=True)


@app.route("/cadastro/<entidade>/editar", methods=["GET", "POST"])
def cadastro_editar(entidade):
    r = exige_login() or exige_perfil("OPERACIONAL")
    if r:
        return r
    cfg = db.ENTIDADES[entidade]
    chave = [request.args.get(c, "") for c in cfg["pk"]]
    if request.method == "POST":
        dados = _coleta_form(cfg)
        try:
            db.atualiza(perfil_atual(), entidade, chave, dados)
            flash("Alteracao gravada.", "ok")
            return redirect(url_for("cadastro_listar", entidade=entidade))
        except Exception as erro:
            flash(db.traduz_erro(erro), "erro")
            return render_template("cadastro_form.html", entidade=entidade,
                                   cfg=cfg, registro=dados, novo=False,
                                   chave=chave)
    registro = db.busca_um(perfil_atual(), entidade, chave)
    if not registro:
        flash("Registro nao encontrado.", "erro")
        return redirect(url_for("cadastro_listar", entidade=entidade))
    return render_template("cadastro_form.html", entidade=entidade, cfg=cfg,
                           registro=registro, novo=False, chave=chave)


@app.route("/cadastro/<entidade>/remover", methods=["POST"])
def cadastro_remover(entidade):
    r = exige_login() or exige_perfil("OPERACIONAL")
    if r:
        return r
    cfg = db.ENTIDADES[entidade]
    chave = [request.form.get(c, "") for c in cfg["pk"]]
    try:
        afetadas, _ = db.remove(perfil_atual(), entidade, chave)
        if afetadas:
            flash("Registro removido.", "ok")
        else:
            flash("Nada foi removido: registro nao encontrado.", "aviso")
    except Exception as erro:
        # Caso tipico: FK com ON DELETE RESTRICT (remover associado que tem
        # propriedade). A mensagem explica o que fazer, em vez de mostrar
        # "Cannot delete or update a parent row".
        flash(db.traduz_erro(erro), "erro")
    return redirect(url_for("cadastro_listar", entidade=entidade))


def _coleta_form(cfg):
    dados = {}
    for coluna in cfg["colunas"]:
        if coluna in request.form:
            valor = request.form.get(coluna, "").strip()
            dados[coluna] = None if valor == "" else valor
    return dados


# ---------------------------------------------------------------------------
# Consultas parametrizadas
# ---------------------------------------------------------------------------
@app.route("/consulta/producao")
def consulta_producao():
    r = exige_login()
    if r:
        return r
    filtros = {
        "data_ini": request.args.get("data_ini", "2024-01-01"),
        "data_fim": request.args.get("data_fim", "2024-12-31"),
        "status": request.args.get("status", "RECEBIDA"),
        "cultura": request.args.get("cultura", ""),
        "kg_minimo": request.args.get("kg_minimo", "0"),
    }
    linhas, erro = [], None
    if request.args:
        try:
            linhas = db.consulta_producao(
                perfil_atual(), filtros["data_ini"], filtros["data_fim"],
                filtros["status"], filtros["cultura"],
                float(filtros["kg_minimo"] or 0))
        except ValueError:
            erro = "A quantidade minima precisa ser um numero."
        except Exception as e:
            erro = db.traduz_erro(e)
    return render_template("consulta_producao.html", filtros=filtros,
                           linhas=linhas, erro=erro,
                           sql=db.SQL_CONSULTA_PRODUCAO)


@app.route("/consulta/associados")
def consulta_associados():
    r = exige_login()
    if r:
        return r
    filtros = {
        "nome": request.args.get("nome", ""),
        "status": request.args.get("status", ""),
        "tipo": request.args.get("tipo", ""),
        "area_minima": request.args.get("area_minima", "0"),
    }
    linhas, erro = [], None
    if request.args:
        try:
            linhas = db.consulta_associados(
                perfil_atual(), filtros["nome"], filtros["status"],
                filtros["tipo"], float(filtros["area_minima"] or 0))
        except ValueError:
            erro = "A area minima precisa ser um numero."
        except Exception as e:
            erro = db.traduz_erro(e)
    return render_template("consulta_associados.html", filtros=filtros,
                           linhas=linhas, erro=erro,
                           sql=db.SQL_CONSULTA_ASSOCIADOS)


# ---------------------------------------------------------------------------
# Relatorio alimentado por VISAO
# ---------------------------------------------------------------------------
@app.route("/relatorio")
def relatorio():
    r = exige_login()
    if r:
        return r
    id_safra = int(request.args.get("id_safra", "0") or 0)
    linhas, safras, erro = [], [], None
    try:
        safras = db.lista_safras(perfil_atual())
        linhas = db.relatorio_safra(perfil_atual(), id_safra)
    except Exception as e:
        erro = db.traduz_erro(e)
    return render_template("relatorio.html", linhas=linhas, safras=safras,
                           id_safra=id_safra, erro=erro)


# ---------------------------------------------------------------------------
# Operacao transacional (B1/B3)
# ---------------------------------------------------------------------------
@app.route("/transacao", methods=["GET", "POST"])
def transacao():
    r = exige_login() or exige_perfil("FINANCEIRO")
    if r:
        return r

    resultado, passos, estado_antes, estado_depois = None, [], None, None
    id_associado = request.form.get("id_associado", "1")
    id_safra = request.form.get("id_safra", "1")
    desconto = request.form.get("desconto", "5")

    if request.method == "POST":
        forcar = request.form.get("acao") == "falha"
        try:
            estado_antes = db.estado_prestacao(perfil_atual(),
                                               int(id_associado), int(id_safra))
            ok, passos, info = db.fecha_prestacao_contas(
                perfil_atual(), int(id_associado), int(id_safra),
                float(desconto), forcar_erro=forcar)
            estado_depois = db.estado_prestacao(perfil_atual(),
                                                int(id_associado), int(id_safra))
            resultado = {"ok": ok, **info}
            if ok:
                flash("Transacao concluida com COMMIT.", "ok")
            else:
                flash(f"Transacao desfeita com ROLLBACK: "
                      f"{info.get('mensagem', '')}", "erro")
        except ValueError:
            flash("Informe numeros validos para associado, safra e desconto.",
                  "erro")

    return render_template("transacao.html", resultado=resultado, passos=passos,
                           estado_antes=estado_antes,
                           estado_depois=estado_depois,
                           id_associado=id_associado, id_safra=id_safra,
                           desconto=desconto)


# ---------------------------------------------------------------------------
# Auditoria (B6)
# ---------------------------------------------------------------------------
@app.route("/auditoria")
def auditoria():
    r = exige_login() or exige_perfil("FINANCEIRO")
    if r:
        return r
    linhas, erro = [], None
    try:
        linhas = db.auditoria_recente(perfil_atual())
    except Exception as e:
        erro = db.traduz_erro(e)
    return render_template("auditoria.html", linhas=linhas, erro=erro)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
