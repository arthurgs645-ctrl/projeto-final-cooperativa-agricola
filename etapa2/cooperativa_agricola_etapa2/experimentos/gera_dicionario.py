"""Gera o dicionario de dados no formato do Anexo A do enunciado.

RESPOSTA A DEVOLUTIVA DA ETAPA 1, criterio C5:
  "complete o dicionario de dados no formato do Anexo A (tipos, restricoes)"

O dicionario e extraido do catalogo do proprio banco (information_schema), e
nao digitado a mao. Assim ele nao pode divergir do esquema real: se uma coluna
mudar de tipo, basta rodar este script de novo.

As observacoes com a regra de negocio (coluna "Observacao" do Anexo A) vem do
dicionario OBSERVACOES abaixo, mantido pela equipe, e sao casadas com as
restricoes encontradas no catalogo.

Uso:
    python experimentos/gera_dicionario.py
Saida:
    docs/A3_dicionario_dados.md  (sobrescrito)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import mysql.connector

import config

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "A3_dicionario_dados.md"

# Regra de negocio associada a cada atributo, no espirito do Anexo A.
OBSERVACOES = {
    ("associado", "id_associado"): "Chave primaria substituta",
    ("associado", "matricula"): "RN01 - nao pode repetir",
    ("associado", "nome"): "Razao social ou nome civil do associado",
    ("associado", "tipo_pessoa"): "RN02 - define qual especializacao se aplica",
    ("associado", "status"): "RN02 - situacao cadastral vigente",
    ("associado", "id_associado_indicador"):
        "RN03 - opcional; nao pode apontar para o proprio associado",
    ("associado_pf", "id_associado"): "Chave primaria e estrangeira (especializacao)",
    ("associado_pf", "cpf"): "RN04 - 11 digitos, nao pode repetir. Dado pessoal",
    ("associado_pf", "data_nascimento"): "RN04 - nao pode ser anterior a 1900. Dado pessoal",
    ("associado_pj", "id_associado"): "Chave primaria e estrangeira (especializacao)",
    ("associado_pj", "cnpj"): "RN05 - 14 digitos, nao pode repetir. Dado da empresa",
    ("associado_pj", "razao_social"): "RN05 - obrigatoria para PJ",
    ("propriedade", "id_propriedade"): "Chave primaria substituta",
    ("propriedade", "id_associado"): "RN06 - cada propriedade tem exatamente um dono",
    ("propriedade", "nome"): "Nome pelo qual a propriedade e conhecida",
    ("propriedade", "registro_rural"): "RN07 - nao pode repetir",
    ("propriedade", "municipio"): "Municipio onde fica a area",
    ("propriedade", "area_hectares"): "RN08 - precisa ser positiva",
    ("propriedade", "status"): "Situacao da regularizacao fundiaria",
    ("cultura", "id_cultura"): "Chave primaria substituta",
    ("cultura", "nome"): "RN09 - nao pode repetir",
    ("cultura", "categoria"): "Agrupamento comercial da cultura",
    ("cultura", "unidade_medida"): "RN09 - unidade em que a producao e medida",
    ("safra", "id_safra"): "Chave primaria substituta",
    ("safra", "descricao"): "RN10 - identificacao da safra, nao pode repetir",
    ("safra", "data_inicio"): "Abertura do periodo produtivo",
    ("safra", "data_fim"): "RN10 - precisa ser posterior a data_inicio",
    ("safra", "status"): "RN10 - estagio do ciclo da safra",
    ("associado_cultura", "id_associado"): "Parte da chave composta",
    ("associado_cultura", "id_cultura"): "Parte da chave composta",
    ("associado_cultura", "area_hectares"): "RN11 - atributo proprio do N:N, positivo",
    ("associado_cultura", "data_inicio"): "Quando o associado passou a produzir a cultura",
    ("safra_cultura", "id_safra"): "Parte da chave composta",
    ("safra_cultura", "id_cultura"): "Parte da chave composta",
    ("safra_cultura", "meta_kg"): "RN12 - atributo proprio do N:N, positivo",
    ("safra_cultura", "preco_base_kg"): "RN12 - preco de referencia, positivo",
    ("lote", "id_safra"): "RN13 - parte da chave da entidade fraca",
    ("lote", "numero_lote"): "RN13 - unico dentro da safra, positivo",
    ("lote", "id_propriedade"): "RN14 - onde o lote e produzido",
    ("lote", "id_cultura"): "RN14 - o que o lote produz",
    ("lote", "quantidade_planejada"): "Precisa ser positiva",
    ("lote", "status"): "Estagio do lote no ciclo produtivo",
    ("historico_associado", "id_historico"): "Chave primaria substituta",
    ("historico_associado", "id_associado"): "A quem o periodo se refere",
    ("historico_associado", "data_inicio"):
        "RN15 - nao repete para o mesmo associado; periodos nao se sobrepoem",
    ("historico_associado", "data_fim"):
        "RN15 - nulo indica periodo vigente; so um aberto por associado",
    ("historico_associado", "situacao"): "RN17 - situacao vigente no periodo",
    ("historico_associado", "motivo"): "Justificativa da mudanca de situacao",
    ("entrega", "id_entrega"): "Chave primaria substituta",
    ("entrega", "id_safra"): "RN16 - parte da referencia ao lote de origem",
    ("entrega", "numero_lote"): "RN16 - parte da referencia ao lote de origem",
    ("entrega", "data_entrega"): "RN20 - precisa cair dentro do periodo da safra",
    ("entrega", "quantidade"): "RN16 - precisa ser positiva",
    ("entrega", "qualidade"): "RN17 - classificacao A, B ou C",
    ("entrega", "preco_unitario_kg"): "Preco pactuado, positivo",
    ("entrega", "status"): "RN17 - estorno e feito por CANCELADA, nunca por DELETE",
    ("prestacao_contas", "id_prestacao"): "Chave primaria substituta",
    ("prestacao_contas", "id_associado"): "RN18 - uma prestacao por associado e safra",
    ("prestacao_contas", "id_safra"): "RN18 - uma prestacao por associado e safra",
    ("prestacao_contas", "total_bruto"): "Soma das entregas recebidas, nao negativa",
    ("prestacao_contas", "total_descontos"): "RN18 - nao pode superar o bruto",
    ("prestacao_contas", "saldo"):
        "RN18 - redundancia derivada deliberada; CHECK garante bruto - descontos",
    ("prestacao_contas", "status"): "Estagio do fechamento financeiro",
    ("movimento_financeiro", "id_movimento"): "Chave primaria substituta",
    ("movimento_financeiro", "id_prestacao"): "RN19 - a qual fechamento pertence",
    ("movimento_financeiro", "data_movimento"): "Data do lancamento",
    ("movimento_financeiro", "valor"): "RN19 - precisa ser positivo",
    ("movimento_financeiro", "tipo"): "RN19 - CREDITO ou DEBITO",
    ("movimento_financeiro", "status"): "Situacao da liquidacao",
    ("movimento_financeiro", "referencia"): "Identificador externo, nao repete",
    ("auditoria", "id_auditoria"): "Chave primaria substituta (Etapa 2)",
    ("auditoria", "tabela"): "Tabela auditada",
    ("auditoria", "operacao"): "INSERT, UPDATE ou DELETE",
    ("auditoria", "chave_registro"): "Identificacao da linha alterada",
    ("auditoria", "campo"): "Coluna alterada; uma linha por campo",
    ("auditoria", "valor_anterior"): "Conteudo antes da alteracao",
    ("auditoria", "valor_novo"): "Conteudo depois da alteracao",
    ("auditoria", "usuario"): "SESSION_USER() - quem se conectou",
    ("auditoria", "data_hora"): "Momento da alteracao",
    ("usuario_app", "id_usuario"): "Chave primaria substituta (Etapa 2)",
    ("usuario_app", "login"): "Identificador de acesso, nao repete",
    ("usuario_app", "nome"): "Nome exibido na interface",
    ("usuario_app", "perfil"): "LEITURA, OPERACIONAL ou FINANCEIRO",
    ("usuario_app", "senha_hash"): "PBKDF2-HMAC-SHA256; nunca a senha em claro",
    ("usuario_app", "senha_sal"): "Sal aleatorio de 16 bytes, unico por usuario",
    ("usuario_app", "algoritmo"): "Algoritmo e custo usados, para migracao futura",
    ("usuario_app", "ativo"): "Permite desativar acesso sem apagar o usuario",
    ("usuario_app", "criado_em"): "Data de criacao do acesso",
}

DESCRICOES_TABELA = {
    "associado": "Pessoa, fisica ou juridica, associada a cooperativa.",
    "associado_pf": "Especializacao do associado pessoa fisica.",
    "associado_pj": "Especializacao do associado pessoa juridica.",
    "propriedade": "Area rural pertencente a um associado.",
    "cultura": "Catalogo de culturas trabalhadas pela cooperativa.",
    "safra": "Ciclo produtivo com periodo definido.",
    "associado_cultura": "Quais culturas cada associado produz e em que area.",
    "safra_cultura": "Meta de producao e preco-base por cultura em cada safra.",
    "lote": "Entidade fraca: porcao de producao identificada dentro da safra.",
    "historico_associado": "Linha do tempo da situacao cadastral do associado.",
    "entrega": "Evento de entrega de producao de um lote.",
    "prestacao_contas": "Fechamento financeiro de um associado em uma safra.",
    "movimento_financeiro": "Lancamento de credito ou debito de uma prestacao.",
    "auditoria": "Trilha de alteracoes gravada pelos gatilhos (Etapa 2).",
    "usuario_app": "Usuarios da aplicacao e seus perfis de acesso (Etapa 2).",
}

ADMIN_SENHA = os.environ.get("COOP_ADMIN_SENHA")
if not ADMIN_SENHA:
    print("Defina COOP_ADMIN_SENHA para ler o catalogo completo.")
    raise SystemExit(1)

con = mysql.connector.connect(
    host=config.DB_HOST, database=config.DB_NAME,
    user=os.environ.get("COOP_ADMIN_USER", "root"), password=ADMIN_SENHA)
cur = con.cursor(dictionary=True)

cur.execute("""
    SELECT TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION, COLUMN_TYPE,
           IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
      FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = %s
     ORDER BY TABLE_NAME, ORDINAL_POSITION
""", (config.DB_NAME,))
colunas = cur.fetchall()

cur.execute("""
    SELECT TABLE_NAME FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
     ORDER BY TABLE_NAME
""", (config.DB_NAME,))
tabelas = [t["TABLE_NAME"] for t in cur.fetchall()]

# restricoes por coluna
cur.execute("""
    SELECT k.TABLE_NAME, k.COLUMN_NAME, k.CONSTRAINT_NAME,
           t.CONSTRAINT_TYPE, k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME
      FROM information_schema.KEY_COLUMN_USAGE k
      JOIN information_schema.TABLE_CONSTRAINTS t
        ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
       AND t.TABLE_NAME = k.TABLE_NAME
       AND t.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
     WHERE k.CONSTRAINT_SCHEMA = %s
""", (config.DB_NAME,))
chaves = cur.fetchall()

cur.execute("""
    SELECT CONSTRAINT_NAME, CHECK_CLAUSE
      FROM information_schema.CHECK_CONSTRAINTS
     WHERE CONSTRAINT_SCHEMA = %s
""", (config.DB_NAME,))
checks = {c["CONSTRAINT_NAME"]: c["CHECK_CLAUSE"] for c in cur.fetchall()}

cur.close()
con.close()


def restricoes_de(tabela, coluna):
    itens = []
    for k in chaves:
        if k["TABLE_NAME"] == tabela and k["COLUMN_NAME"] == coluna:
            if k["CONSTRAINT_TYPE"] == "PRIMARY KEY":
                itens.append("PK")
            elif k["CONSTRAINT_TYPE"] == "UNIQUE":
                itens.append(f"UNIQUE ({k['CONSTRAINT_NAME']})")
            elif k["CONSTRAINT_TYPE"] == "FOREIGN KEY":
                itens.append(
                    f"FK -> {k['REFERENCED_TABLE_NAME']}."
                    f"{k['REFERENCED_COLUMN_NAME']} ({k['CONSTRAINT_NAME']})")
    for nome, clausula in checks.items():
        if coluna in clausula and nome.startswith("ck_"):
            # heuristica: o CHECK cita a coluna e pertence a esta tabela pelo prefixo
            if nome.split("_")[1] in tabela or tabela.startswith(nome.split("_")[1]):
                itens.append(f"CHECK {nome}")
    return "; ".join(dict.fromkeys(itens)) or "-"


linhas = []
linhas.append("# A3 — Dicionário de Dados")
linhas.append("")
linhas.append("**Projeto:** Cooperativa Agrícola — Projeto Final  ")
linhas.append("**Disciplina:** Laboratório de Banco de Dados — GPE17M40053  ")
linhas.append("**SGBD:** MySQL 8.0  ")
linhas.append("**Equipe:** Artur Gabriel Queiroz de Morais; Arthur Gonçalves Silva; "
              "Arthur Marques Cipriano; Arthur Mélo Mesquita Mitrovich; "
              "Fabrício Nogueira de Brito")
linhas.append("")
linhas.append("> Documento gerado a partir do catálogo do próprio banco "
              "(`information_schema`) por `experimentos/gera_dicionario.py`, "
              "no formato do Anexo A do enunciado. Gerar em vez de digitar "
              "garante que o dicionário não divirja do esquema real.")
linhas.append("")
linhas.append("Atende à devolutiva da Etapa 1, critério C5: "
              "*\"complete o dicionário de dados no formato do Anexo A "
              "(tipos, restrições)\"*.")
linhas.append("")

for tabela in tabelas:
    linhas.append(f"## {tabela}")
    linhas.append("")
    linhas.append(DESCRICOES_TABELA.get(tabela, ""))
    linhas.append("")
    linhas.append("| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |")
    linhas.append("|---|---|---|---|---|---|")
    for c in colunas:
        if c["TABLE_NAME"] != tabela:
            continue
        obs = OBSERVACOES.get((tabela, c["COLUMN_NAME"]), "")
        descricao = obs.split(" - ")[-1] if " - " in obs else obs
        regra = obs.split(" - ")[0] if obs.startswith("RN") else ""
        obrig = "Não" if c["IS_NULLABLE"] == "YES" else "Sim"
        extra = f" ({c['EXTRA']})" if c["EXTRA"] else ""
        linhas.append(
            f"| `{c['COLUMN_NAME']}` | {descricao or '—'} "
            f"| {c['COLUMN_TYPE']}{extra} | {obrig} "
            f"| {restricoes_de(tabela, c['COLUMN_NAME'])} "
            f"| {regra or '—'} |")
    linhas.append("")

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print(f"Dicionario gerado: {SAIDA}")
print(f"{len(tabelas)} tabelas, {len(colunas)} colunas documentadas")
