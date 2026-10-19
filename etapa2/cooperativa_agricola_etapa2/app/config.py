"""Configuracao da aplicacao.

B2 - Credenciais fora do codigo-fonte.

Nenhuma senha aparece neste arquivo. Tudo e lido de variaveis de ambiente,
carregadas de um arquivo .env que esta no .gitignore. O arquivo versionado e o
.env.example, que traz apenas os nomes das variaveis.

Se uma variavel obrigatoria faltar, a aplicacao falha na inicializacao com uma
mensagem clara, em vez de tentar conectar com um valor padrao inseguro.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _carrega_env() -> None:
    """Le o .env da raiz do projeto, se existir.

    Implementado a mao para nao adicionar dependencia de python-dotenv ao
    projeto. Linhas vazias e comentarios sao ignorados; valores podem estar
    entre aspas.
    """
    caminho = RAIZ / ".env"
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave.strip(), valor)


_carrega_env()


def _obrigatoria(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(
            f"Variavel de ambiente {nome} nao definida. "
            f"Copie .env.example para .env e preencha os valores."
        )
    return valor


DB_HOST = os.environ.get("COOP_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("COOP_DB_PORT", "3306"))
DB_NAME = os.environ.get("COOP_DB_NAME", "cooperativa_agricola")

# Uma conta de banco por perfil de acesso. A aplicacao conecta com a conta
# correspondente ao perfil do usuario autenticado, de modo que o proprio SGBD
# recusa qualquer operacao fora do perfil - mesmo que houvesse uma falha na
# verificacao feita pela aplicacao. E a segunda linha de defesa.
CONTAS = {
    "LEITURA": {
        "user": os.environ.get("COOP_USER_LEITURA", "app_leitura"),
        "password": _obrigatoria("COOP_SENHA_LEITURA"),
    },
    "OPERACIONAL": {
        "user": os.environ.get("COOP_USER_OPERACIONAL", "app_operacional"),
        "password": _obrigatoria("COOP_SENHA_OPERACIONAL"),
    },
    "FINANCEIRO": {
        "user": os.environ.get("COOP_USER_FINANCEIRO", "app_financeiro"),
        "password": _obrigatoria("COOP_SENHA_FINANCEIRO"),
    },
}

SECRET_KEY = os.environ.get("COOP_SECRET_KEY", "chave-local-de-desenvolvimento")
