"""Cria os usuarios de demonstracao da aplicacao com senha protegida.

B5 - evidencia de que a senha nunca e gravada em texto claro.

Uso:
    python app/seed_usuarios.py

O script e idempotente: apaga e recria os tres usuarios de demonstracao.
Note que cada execucao gera um SAL diferente, portanto o hash gravado muda a
cada execucao mesmo com a mesma senha. Isso e justamente o efeito esperado do
sal, e o script imprime os dois hashes para tornar o efeito visivel.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth
import db

USUARIOS = [
    ("leitura",    "Luiza (consulta)",       "LEITURA",     "leitura123"),
    ("patio",      "Pedro (patio)",          "OPERACIONAL", "patio123"),
    ("tesouraria", "Tereza (tesouraria)",    "FINANCEIRO",  "tesouraria123"),
]

# O seed precisa de INSERT em usuario_app, que nenhuma conta de aplicacao tem
# (de proposito: a aplicacao nao cria usuarios). Por isso ele usa a conta
# administrativa, informada por linha de comando ou variavel de ambiente.
import os

import mysql.connector

import config

ADMIN_USER = os.environ.get("COOP_ADMIN_USER", "root")
ADMIN_SENHA = os.environ.get("COOP_ADMIN_SENHA")

if not ADMIN_SENHA:
    print("Defina COOP_ADMIN_SENHA com a senha do usuario administrativo do "
          "MySQL antes de rodar o seed.")
    raise SystemExit(1)

con = mysql.connector.connect(
    host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME,
    user=ADMIN_USER, password=ADMIN_SENHA, autocommit=False,
)
cur = con.cursor(prepared=True)

print("Gerando credenciais com PBKDF2-HMAC-SHA256, 260.000 iteracoes\n")

for login, nome, perfil, senha in USUARIOS:
    senha_hash, sal, algoritmo = auth.cria_credencial(senha)

    cur.execute("DELETE FROM usuario_app WHERE login = %s", (login,))
    cur.execute("""
        INSERT INTO usuario_app (login, nome, perfil, senha_hash, senha_sal,
                                 algoritmo, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, 1)
    """, (login, nome, perfil, senha_hash, sal, algoritmo))

    print(f"  {login:<12} perfil {perfil}")
    print(f"    sal  : {sal}")
    print(f"    hash : {senha_hash[:48]}...")
    print(f"    (a senha '{senha}' nao aparece em nenhuma coluna)\n")

con.commit()
cur.close()
con.close()

# Demonstracao do efeito do sal: a mesma senha, derivada duas vezes com sais
# diferentes, produz hashes completamente diferentes.
h1, s1, _ = auth.cria_credencial("senha-igual")
h2, s2, _ = auth.cria_credencial("senha-igual")
print("Efeito do sal - mesma senha, dois cadastros diferentes:")
print(f"  sal 1 {s1} -> {h1[:32]}...")
print(f"  sal 2 {s2} -> {h2[:32]}...")
print(f"  hashes iguais? {h1 == h2}")
