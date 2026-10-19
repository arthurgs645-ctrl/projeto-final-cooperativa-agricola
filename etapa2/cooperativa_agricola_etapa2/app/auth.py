"""Autenticacao dos usuarios da aplicacao.

B5 - Senhas armazenadas com funcao de hash e sal.

Decisoes:

- Algoritmo: PBKDF2-HMAC-SHA256 com 260.000 iteracoes. E funcao de derivacao
  deliberadamente lenta: o custo e irrelevante para um login legitimo (alguns
  centesimos de segundo) e multiplica por centenas de milhares o custo de quem
  tenta adivinhar senhas em massa. Esta na biblioteca padrao do Python
  (hashlib), sem dependencia externa.

- Sal: 16 bytes aleatorios por usuario, vindos de os.urandom. O sal nao e
  segredo - fica ao lado do hash no banco. Sua funcao e garantir que duas
  pessoas com a mesma senha tenham hashes diferentes, o que inutiliza tabelas
  pre-calculadas (rainbow tables) e impede descobrir senhas repetidas apenas
  comparando as colunas.

- Comparacao: hmac.compare_digest, que gasta o mesmo tempo independentemente de
  onde os bytes diferem. Uma comparacao comum com == vaza, pelo tempo de
  resposta, quantos bytes iniciais estavam corretos.

O que NUNCA acontece aqui: gravar senha em texto claro, e usar hash simples
(MD5, SHA-1 ou SHA-256 puro), que sao rapidos demais e foram feitos para
integridade, nao para proteger senha.
"""

import hashlib
import hmac
import os

ITERACOES = 260_000
ALGORITMO = f"pbkdf2_sha256${ITERACOES}"


def gera_sal() -> str:
    return os.urandom(16).hex()


def calcula_hash(senha: str, sal_hex: str, iteracoes: int = ITERACOES) -> str:
    derivado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        bytes.fromhex(sal_hex),
        iteracoes,
    )
    return derivado.hex()


def cria_credencial(senha: str):
    """Devolve (hash, sal, algoritmo) para gravar em usuario_app."""
    sal = gera_sal()
    return calcula_hash(senha, sal), sal, ALGORITMO


def confere(senha_digitada: str, hash_guardado: str, sal_hex: str,
            algoritmo: str = ALGORITMO) -> bool:
    try:
        iteracoes = int(algoritmo.split("$")[1])
    except (IndexError, ValueError):
        iteracoes = ITERACOES
    calculado = calcula_hash(senha_digitada, sal_hex, iteracoes)
    return hmac.compare_digest(calculado, hash_guardado)
