"""Teste de ponta a ponta da aplicacao.

Percorre o checklist do Anexo C do enunciado pela interface HTTP real, como um
usuario faria pelo navegador, e grava a evidencia em
experimentos/resultados/B1_teste_aplicacao.txt.

Uso (com a aplicacao rodando em http://127.0.0.1:5000):
    python experimentos/teste_aplicacao.py
"""

import io
import re
import sys
from datetime import date
from pathlib import Path

import requests

BASE = "http://127.0.0.1:5000"
SAIDA = (Path(__file__).resolve().parent / "resultados" /
         "B1_teste_aplicacao.txt")

relatorio = io.StringIO()
contador = {"ok": 0, "falha": 0}


def escreve(texto=""):
    print(texto)
    relatorio.write(texto + "\n")


def verifica(descricao, condicao, detalhe=""):
    marca = "PASSOU" if condicao else "FALHOU"
    contador["ok" if condicao else "falha"] += 1
    escreve(f"  [{marca}] {descricao}")
    if detalhe:
        escreve(f"           {detalhe}")
    return condicao


def entra(sessao, login, senha):
    r = sessao.post(f"{BASE}/login", data={"login": login, "senha": senha},
                    allow_redirects=True)
    return r


def mensagens(html):
    """Extrai o texto das mensagens flash renderizadas."""
    return re.findall(r'<div class="(?:erro|ok|aviso)">([^<]+)</div>', html)


escreve("=" * 74)
escreve("B1 - TESTE DE PONTA A PONTA DA APLICACAO")
escreve(f"Executado em {date.today().strftime('%d/%m/%Y')} contra {BASE}")
escreve("=" * 74)

# ---------------------------------------------------------------- AUTENTICACAO
escreve("\n1. AUTENTICACAO (B5)")

s_anon = requests.Session()
r = s_anon.get(f"{BASE}/", allow_redirects=True)
verifica("Acesso sem login e redirecionado para a tela de entrada",
         "Entrar no sistema" in r.text)

s_ruim = requests.Session()
r = entra(s_ruim, "patio", "senha-errada")
verifica("Senha errada e recusada", "Login ou senha" in r.text)

r = entra(s_ruim, "nao-existe", "qualquer")
msgs = mensagens(r.text)
verifica("Login inexistente devolve a MESMA mensagem da senha errada",
         any("Login ou senha" in m for m in msgs),
         "evita revelar quais logins existem")

s_leitura = requests.Session()
r = entra(s_leitura, "leitura", "leitura123")
verifica("Login LEITURA aceito", "perfil <strong>LEITURA" in r.text)

s_patio = requests.Session()
r = entra(s_patio, "patio", "patio123")
verifica("Login OPERACIONAL aceito", "perfil <strong>OPERACIONAL" in r.text)

s_tesouraria = requests.Session()
r = entra(s_tesouraria, "tesouraria", "tesouraria123")
verifica("Login FINANCEIRO aceito", "perfil <strong>FINANCEIRO" in r.text)

# ------------------------------------------------------------ CONTROLE DE ACESSO
escreve("\n2. CONTROLE DE ACESSO POR PERFIL (B5)")

r = s_leitura.get(f"{BASE}/transacao", allow_redirects=True)
verifica("LEITURA nao acessa a tela de transacao",
         any("nao tem acesso" in m for m in mensagens(r.text)))

r = s_patio.get(f"{BASE}/auditoria", allow_redirects=True)
verifica("OPERACIONAL nao acessa a auditoria",
         any("nao tem acesso" in m for m in mensagens(r.text)))

r = s_leitura.get(f"{BASE}/cadastro/cultura/novo", allow_redirects=True)
verifica("LEITURA nao acessa o formulario de cadastro",
         any("nao tem acesso" in m for m in mensagens(r.text)))

r = s_tesouraria.get(f"{BASE}/transacao")
verifica("FINANCEIRO acessa a tela de transacao",
         "Operação transacional" in r.text or "transacional" in r.text)

# ---------------------------------------------------------------------- CRUD
escreve("\n3. CRUD DE QUATRO ENTIDADES (B1)")

for entidade in ["associado", "propriedade", "cultura", "lote"]:
    r = s_patio.get(f"{BASE}/cadastro/{entidade}")
    verifica(f"Listagem de {entidade} responde",
             r.status_code == 200 and "<table>" in r.text)

nome_cultura = f"Cultura Teste {date.today().strftime('%H%M%S')}"
r = s_patio.post(f"{BASE}/cadastro/cultura/novo",
                 data={"nome": nome_cultura, "categoria": "GRAO",
                       "unidade_medida": "KG"}, allow_redirects=True)
verifica("CREATE: cultura nova cadastrada",
         any("cadastrad" in m.lower() for m in mensagens(r.text)))

r = s_patio.get(f"{BASE}/cadastro/cultura")
verifica("READ: a cultura criada aparece na listagem", nome_cultura in r.text)

id_novo = None
m = re.search(r"<td>(\d+)</td>\s*<td>" + re.escape(nome_cultura), r.text)
if m:
    id_novo = m.group(1)

if id_novo:
    r = s_patio.post(f"{BASE}/cadastro/cultura/editar?id_cultura={id_novo}",
                     data={"nome": nome_cultura + " (alterada)",
                           "categoria": "GRAO", "unidade_medida": "SC"},
                     allow_redirects=True)
    verifica("UPDATE: alteracao gravada",
             any("gravad" in m.lower() for m in mensagens(r.text)))

    r = s_patio.post(f"{BASE}/cadastro/cultura/remover",
                     data={"id_cultura": id_novo}, allow_redirects=True)
    verifica("DELETE: registro removido",
             any("removido" in m.lower() for m in mensagens(r.text)))
else:
    verifica("UPDATE/DELETE: id da cultura criada localizado", False,
             "nao foi possivel localizar o id na listagem")

# --------------------------------------------------- TRATAMENTO DE RESTRICAO
escreve("\n4. TRATAMENTO DE ERRO DE RESTRICAO (B1)")

r = s_patio.post(f"{BASE}/cadastro/cultura/novo",
                 data={"nome": "Soja", "categoria": "GRAO",
                       "unidade_medida": "KG"}, allow_redirects=True)
msgs = mensagens(r.text)
verifica("UNIQUE violado devolve frase de usuario, nao excecao do driver",
         any("ja existe" in m.lower() for m in msgs),
         f"mensagem exibida: {msgs[0] if msgs else '(nenhuma)'}")
verifica("A mensagem NAO contem texto cru do MySQL",
         not any(("Duplicate entry" in m or "1062" in m) for m in msgs))

r = s_patio.post(f"{BASE}/cadastro/cultura/novo",
                 data={"nome": f"Teste Area {date.today()}",
                       "categoria": "", "unidade_medida": ""},
                 allow_redirects=True)
msgs = mensagens(r.text)
verifica("NOT NULL violado tambem e traduzido",
         any(("branco" in m.lower() or "nao foi possivel" in m.lower())
             for m in msgs),
         f"mensagem exibida: {msgs[0] if msgs else '(nenhuma)'}")

r = s_patio.post(f"{BASE}/cadastro/associado/remover",
                 data={"id_associado": "1"}, allow_redirects=True)
msgs = mensagens(r.text)
verifica("FK RESTRICT violado explica o que fazer",
         any("dependentes" in m.lower() for m in msgs),
         f"mensagem exibida: {msgs[0] if msgs else '(nenhuma)'}")

r = s_patio.post(f"{BASE}/cadastro/lote/novo",
                 data={"id_safra": "1", "numero_lote": "9999",
                       "id_propriedade": "1", "id_cultura": "1",
                       "quantidade_planejada": "-5", "status": "PLANEJADO"},
                 allow_redirects=True)
msgs = mensagens(r.text)
verifica("CHECK violado (quantidade negativa) e traduzido",
         any(("maior que zero" in m.lower() or "validacao" in m.lower())
             for m in msgs),
         f"mensagem exibida: {msgs[0] if msgs else '(nenhuma)'}")

# ------------------------------------------------------ CONSULTAS E RELATORIO
escreve("\n5. CONSULTAS PARAMETRIZADAS E RELATORIO (B1)")

r = s_leitura.get(f"{BASE}/consulta/producao",
                  params={"data_ini": "2024-01-01", "data_fim": "2024-12-31",
                          "status": "RECEBIDA", "cultura": "",
                          "kg_minimo": "0"})
verifica("Consulta 1 (producao) responde com resultado",
         r.status_code == 200 and "linha(s)" in r.text)

r = s_leitura.get(f"{BASE}/consulta/associados",
                  params={"nome": "", "status": "ATIVO", "tipo": "",
                          "area_minima": "0"})
verifica("Consulta 2 (associados) responde com resultado",
         r.status_code == 200 and "linha(s)" in r.text)

r = s_leitura.get(f"{BASE}/relatorio", params={"id_safra": "1"})
verifica("Relatorio alimentado pela visao responde",
         r.status_code == 200 and "linha(s)" in r.text)

# ------------------------------------------------------------ INJECAO DE SQL
escreve("\n6. RESISTENCIA A INJECAO DE SQL (B2)")

cargas = [
    ("' OR '1'='1", "tautologia classica"),
    ("'; DROP TABLE cultura; --", "tentativa de destruir tabela"),
    ("' UNION SELECT cpf,1,1,1,1,1,1,1,1 FROM associado_pf -- ",
     "tentativa de extrair CPF por UNION"),
]
for carga, descricao in cargas:
    r = s_leitura.get(f"{BASE}/consulta/associados",
                      params={"nome": carga, "status": "", "tipo": "",
                              "area_minima": "0"})
    sem_vazamento = (r.status_code == 200
                     and "Nenhum resultado" in r.text
                     and "SQL syntax" not in r.text)
    verifica(f"Resiste a: {descricao}", sem_vazamento,
             f"entrada: {carga}")

r = s_leitura.get(f"{BASE}/consulta/associados",
                  params={"nome": "", "status": "", "tipo": "",
                          "area_minima": "0"})
verifica("A tabela cultura continua existindo apos as tentativas",
         s_patio.get(f"{BASE}/cadastro/cultura").status_code == 200)

# ------------------------------------------------------------------ TRANSACAO
escreve("\n7. OPERACAO TRANSACIONAL (B1/B3)")

r = s_tesouraria.post(f"{BASE}/transacao",
                      data={"id_associado": "1", "id_safra": "1",
                            "desconto": "5", "acao": "sucesso"},
                      allow_redirects=True)
sucesso_ok = "COMMIT" in r.text
verifica("Caminho normal termina em COMMIT", sucesso_ok)
verifica("As duas tabelas aparecem no quadro antes/depois",
         "total créditos" in r.text or "total creditos" in r.text)

# mesmo associado do teste anterior: precisa ter entregas recebidas, senao a
# transacao para antes de escrever e a demonstracao do ROLLBACK perde o sentido
r = s_tesouraria.post(f"{BASE}/transacao",
                      data={"id_associado": "1", "id_safra": "1",
                            "desconto": "5", "acao": "falha"},
                      allow_redirects=True)
verifica("Caminho com falha provocada termina em ROLLBACK", "ROLLBACK" in r.text)
verifica("A falha e explicada em linguagem de usuario",
         "descontos nao podem superar" in r.text.lower()
         or "descontos não podem superar" in r.text.lower())

# ------------------------------------------------------------------ AUDITORIA
escreve("\n8. GATILHOS DE AUDITORIA (B6)")

# a segunda execucao para o mesmo associado faz UPDATE e dispara o gatilho
s_tesouraria.post(f"{BASE}/transacao",
                  data={"id_associado": "1", "id_safra": "1",
                        "desconto": "7", "acao": "sucesso"},
                  allow_redirects=True)
r = s_tesouraria.get(f"{BASE}/auditoria")
verifica("Trilha de auditoria registrou alteracao em prestacao_contas",
         "prestacao_contas" in r.text)
verifica("A trilha mostra valor anterior e valor novo",
         "valor anterior" in r.text and "valor novo" in r.text)

# ---------------------------------------------------------------------- FIM
escreve("")
escreve("=" * 74)
escreve(f"RESULTADO: {contador['ok']} passaram, {contador['falha']} falharam")
escreve("=" * 74)

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text(relatorio.getvalue(), encoding="utf-8")
print(f"\nEvidencia gravada em {SAIDA}")

sys.exit(1 if contador["falha"] else 0)
