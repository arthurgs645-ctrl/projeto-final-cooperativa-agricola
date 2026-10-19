# Projeto Final — Cooperativa Agrícola

**Laboratório de Banco de Dados — GPE17M40053 — 2026/2**
Universidade Católica de Brasília — Bacharelado em Engenharia de Software
Professor: Samuel Novais Moura Júnior

## Equipe

- Artur Gabriel Queiroz de Morais
- Arthur Gonçalves Silva
- Arthur Marques Cipriano
- Arthur Mélo Mesquita Mitrovich
- Fabrício Nogueira de Brito

## Tema

Cooperativa agrícola — safras, lotes rastreáveis, associados com histórico de entregas e prestação de contas.

**SGBD:** MySQL 8.0 · **Aplicação:** Python 3 com Flask

## Organização do repositório

```text
projeto-final/
├── etapa1/cooperativa_agricola_etapa1/   Modelagem e construção do banco (N1)
└── etapa2/cooperativa_agricola_etapa2/   Operação, interface e desempenho (N2)
```

### Etapa 1 — Do modelo conceitual ao banco construído

MER conceitual, modelo lógico normalizado, dicionário de dados, script físico (DDL) com todas as restrições nomeadas, carga de dados sintéticos e 15 consultas de verificação.

### Etapa 2 — Operação, interface e desempenho

Aplicação web que exercita o banco, estudo de concorrência com sessões simultâneas, otimização medida com `EXPLAIN`, controle de acesso por perfil, gatilhos de auditoria e documentação de projeto físico.

| Artefato | Onde |
|---|---|
| B1 — Aplicação com interface | [`etapa2/.../app/`](etapa2/cooperativa_agricola_etapa2/app/) |
| B2 — Camada de acesso e injeção de SQL | [`app/db.py`](etapa2/cooperativa_agricola_etapa2/app/db.py) |
| B3 — Transações e concorrência | [`experimentos/concorrencia.py`](etapa2/cooperativa_agricola_etapa2/experimentos/concorrencia.py) |
| B4 — Otimização | [`sql/08_otimizacao_indices.sql`](etapa2/cooperativa_agricola_etapa2/sql/08_otimizacao_indices.sql) |
| B5 — Segurança e perfis | [`sql/06_seguranca_perfis.sql`](etapa2/cooperativa_agricola_etapa2/sql/06_seguranca_perfis.sql) |
| B6 — Gatilhos e auditoria | [`sql/05_triggers_auditoria.sql`](etapa2/cooperativa_agricola_etapa2/sql/05_triggers_auditoria.sql) |
| B7 e B8 — Projeto físico e relatório | [`docs/relatorio-etapa2.pdf`](etapa2/cooperativa_agricola_etapa2/docs/relatorio-etapa2.pdf) |
| Resposta à devolutiva da Etapa 1 | [`sql/09_reforco_restricoes.sql`](etapa2/cooperativa_agricola_etapa2/sql/09_reforco_restricoes.sql) |

## Como executar

As instruções completas, para máquina limpa, estão em [`etapa2/cooperativa_agricola_etapa2/README.md`](etapa2/cooperativa_agricola_etapa2/README.md).

Resumo:

```bash
cd etapa2/cooperativa_agricola_etapa2
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p < sql/02_carga.sql
mysql -u root -p < sql/04_views.sql
mysql -u root -p < sql/05_triggers_auditoria.sql
mysql -u root -p < sql/06_seguranca_perfis.sql
mysql -u root -p < sql/09_reforco_restricoes.sql

copy .env.example .env     # preencha as senhas
pip install flask mysql-connector-python
python app/seed_usuarios.py
python app/app.py
```

## Evidências

Todos os números do relatório vêm de execução real contra o banco, e as saídas estão versionadas em [`etapa2/.../experimentos/resultados/`](etapa2/cooperativa_agricola_etapa2/experimentos/resultados/):

| Evidência | Resultado |
|---|---|
| Teste da aplicação ponta a ponta | 36 verificações, 0 falhas |
| Perfis de acesso com login real | 11 testes, 0 divergências |
| Restrições reforçadas (devolutiva C3) | 10 testes, 0 divergências |
| Reconstrução do banco do zero | 9 scripts, 0 erros |
| Concorrência | bloqueio, MVCC e deadlock reais |
| Otimização | 3 consultas, `EXPLAIN` antes e depois |

## Credenciais

Nenhuma senha está versionada. O arquivo `.env` está no `.gitignore`; o que se versiona é o `.env.example`, só com os nomes das variáveis.

## Declaração de uso de IA

Declarada na seção 10 do relatório da Etapa 2, conforme o item 9 do enunciado.
