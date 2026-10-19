# Projeto Final — Cooperativa Agrícola — Etapa 2

**Laboratório de Banco de Dados — GPE17M40053 — 2026/2**
*(o código da turma foi corrigido nesta etapa: a Etapa 1 trazia `GPE17M40083`, apontado na devolutiva, critério C5)*

## Equipe

- Artur Gabriel Queiroz de Morais
- Arthur Gonçalves Silva
- Arthur Marques Cipriano
- Arthur Mélo Mesquita Mitrovich
- Fabrício Nogueira de Brito

## Tema

Cooperativa agrícola — safras, lotes rastreáveis, associados com histórico de entregas e prestação de contas.

## O que a Etapa 2 acrescenta

A Etapa 1 projetou e construiu o banco. A Etapa 2 o coloca em operação: uma aplicação web o exercita, duas sessões simultâneas disputam a mesma linha, três consultas críticas são medidas antes e depois de índice, e o acesso passa a ser controlado por perfil.

| Artefato | Onde |
|---|---|
| B1 — Aplicação com interface | `app/` |
| B2 — Camada de acesso e injeção de SQL | `app/db.py`, `experimentos/injecao_sql.py` |
| B3 — Transações e concorrência | `app/db.py` (`fecha_prestacao_contas`), `experimentos/concorrencia.py` |
| B4 — Otimização | `sql/08_otimizacao_indices.sql`, `experimentos/resultados/B4_explain.txt` |
| B5 — Segurança e perfis | `sql/06_seguranca_perfis.sql`, `app/auth.py` |
| B6 — Gatilhos e auditoria | `sql/05_triggers_auditoria.sql` |
| B7 — Projeto físico | `docs/relatorio-etapa2.md`, seção 8 |
| B8 — Relatório consolidado | `docs/relatorio-etapa2.pdf` |
| Resposta à devolutiva da Etapa 1 | `docs/relatorio-etapa2.md`, seção 1; `sql/09_reforco_restricoes.sql` |

## SGBD e linguagem

**MySQL 8.0+** (o mesmo da Etapa 1, sem troca entre etapas) e **Python 3.11+ com Flask**.

O esquema é autoral: nenhuma tabela é gerada por ORM. A aplicação usa SQL escrito à mão, com consultas parametrizadas, e o SQL das consultas do B4 está visível para que o plano de execução possa ser analisado.

## Estrutura

```text
cooperativa_agricola_etapa2/
├── README.md
├── .env.example                  modelo de configuração (o .env real não é versionado)
├── .gitignore
├── app/
│   ├── app.py                    rotas Flask
│   ├── db.py                     camada de acesso: prepared statements e tradução de erro
│   ├── auth.py                   PBKDF2-HMAC-SHA256 com sal
│   ├── config.py                 leitura das credenciais do ambiente
│   ├── seed_usuarios.py          cria os usuários de demonstração com senha protegida
│   └── templates/
│       ├── base.html             layout e navegação
│       ├── login.html
│       ├── inicio.html
│       ├── cadastro_lista.html   listagem genérica do CRUD
│       ├── cadastro_form.html    formulário genérico do CRUD
│       ├── consulta_producao.html
│       ├── consulta_associados.html
│       ├── relatorio.html        alimentado por visão
│       ├── transacao.html        operação multitabela
│       └── auditoria.html
├── sql/
│   ├── 01_ddl.sql                Etapa 1, sem alteração
│   ├── 02_carga.sql              Etapa 1, sem alteração
│   ├── 03_consultas.sql          Etapa 1, sem alteração
│   ├── 04_views.sql              relatório consolidado e visões de restrição
│   ├── 05_triggers_auditoria.sql tabela de auditoria e 2 gatilhos
│   ├── 06_seguranca_perfis.sql   3 papéis, GRANT/REVOKE, contas da aplicação
│   ├── 07_carga_volume.sql       carga para o estudo de desempenho (reversível)
│   ├── 08_otimizacao_indices.sql índices definidos a partir da medição
│   └── 09_reforco_restricoes.sql resposta à devolutiva C3 (7 gatilhos de regra)
├── docs/
│   ├── relatorio-etapa2.pdf      relatório consolidado (entrega)
│   ├── relatorio-etapa2.md       fonte do relatório
│   ├── A1_escopo_regras.md       Etapa 1 revisada
│   ├── A3_dicionario_dados.md    regerado no formato do Anexo A
│   ├── A4_modelo_logico.md
│   ├── A5_normalizacao.md
│   ├── mer-conceitual.drawio     fonte editável do diagrama
│   ├── mer-conceitual.pdf
│   ├── modelo-logico.pdf
│   └── relatorio-etapa1.pdf
└── experimentos/
    ├── teste_aplicacao.py        36 verificações pela interface HTTP
    ├── concorrencia.py           duas sessões simultâneas
    ├── injecao_sql.py            vulnerável x parametrizada, lado a lado
    ├── gera_dicionario.py        extrai o dicionário do information_schema
    └── resultados/
        ├── B1_teste_aplicacao.txt
        ├── B2_injecao_sql.txt
        ├── B3_concorrencia.txt
        ├── B4_explain.txt
        ├── B5_teste_perfis.txt
        ├── B7_armazenamento.txt
        └── C3_reforco_restricoes.txt
```

> Os scripts `01_ddl.sql`, `02_carga.sql` e `03_consultas.sql` são da Etapa 1 e seguem válidos sem alteração. A numeração desta etapa continua a partir de 04 de propósito, para deixar claro que nada da Etapa 1 foi reescrito.

## Como executar em máquina limpa

### 1. Banco

Com o MySQL 8.0 rodando, execute **na ordem**:

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p < sql/02_carga.sql
mysql -u root -p < sql/04_views.sql
mysql -u root -p < sql/05_triggers_auditoria.sql
mysql -u root -p < sql/06_seguranca_perfis.sql
mysql -u root -p < sql/09_reforco_restricoes.sql
```

Para reproduzir o estudo de desempenho do B4 (opcional — eleva `entrega` a 200 mil linhas):

```bash
mysql -u root -p < sql/07_carga_volume.sql
mysql -u root -p < sql/08_otimizacao_indices.sql
```

Para desfazer a carga de volume: `DELETE FROM entrega WHERE id_entrega > 160;`

### 2. Configuração

```bash
cp .env.example .env     # no Windows: copy .env.example .env
```

Preencha o `.env` com as senhas definidas em `sql/06_seguranca_perfis.sql`. Esse arquivo não é versionado.

### 3. Dependências

```bash
pip install flask mysql-connector-python
```

### 4. Usuários da aplicação

```bash
set COOP_ADMIN_SENHA=sua-senha-root      # Windows
export COOP_ADMIN_SENHA=sua-senha-root   # Linux/macOS
python app/seed_usuarios.py
```

### 5. Aplicação

```bash
python app/app.py
```

Abra `http://127.0.0.1:5000`.

| Login | Senha | Perfil |
|---|---|---|
| `leitura` | `leitura123` | LEITURA |
| `patio` | `patio123` | OPERACIONAL |
| `tesouraria` | `tesouraria123` | FINANCEIRO |

## Como reproduzir os experimentos

```bash
python experimentos/teste_aplicacao.py   # com a aplicação rodando
python experimentos/injecao_sql.py
python experimentos/concorrencia.py      # exige COOP_ADMIN_SENHA
python experimentos/gera_dicionario.py   # exige COOP_ADMIN_SENHA
```

Cada um grava sua evidência em `experimentos/resultados/`.

## Roteiro da demonstração ao vivo

| Momento | O que mostrar | Onde |
|---|---|---|
| Contexto | domínio e o que mudou desde a Etapa 1 | relatório, seção 1 |
| CRUD e consultas | cadastrar cultura, consultar produção, abrir relatório | menu da aplicação |
| Transação | executar fechamento normal, depois com falha provocada | tela *Fechar prestação* |
| Restrições em ação | tentar remover associado que tem propriedades | tela *Associados* |
| Desempenho e acesso | `EXPLAIN` antes/depois; entrar com dois perfis diferentes | `B4_explain.txt` e troca de login |

Antes de apresentar: banco povoado, aplicação rodando, e duas sessões de terminal abertas para o experimento de concorrência.

## Declaração de uso de IA

Mantida e atualizada na seção 10 do relatório, conforme o item 9 do enunciado.
