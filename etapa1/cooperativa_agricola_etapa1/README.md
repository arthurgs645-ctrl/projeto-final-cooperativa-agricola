# Projeto Final — Cooperativa Agrícola

**Laboratório de Banco de Dados — GPE17M40083 — 2026/2**

## Equipe

- Artur Gabriel Queiroz de Morais
- Arthur Gonçalves Silva
- Arthur Marques Cipriano
- Arthur Mélo Mesquita Mitrovich
- Fabrício Nogueira de Brito

## Tema

**Cooperativa agrícola — safras, lotes rastreáveis, associados com histórico de entregas e prestação de contas.**

## SGBD

**MySQL 8.0+**, desenvolvido e testado conceitualmente para execução no MySQL Workbench 8.0.

## Objetivo da Etapa 1

Construir um banco de dados completo para representar o núcleo operacional de uma cooperativa agrícola: associados, propriedades, culturas, safras, lotes, entregas, histórico e prestação de contas.

## Requisitos de complexidade atendidos

| Requisito | Implementação |
|---|---|
| 8 entidades | O modelo possui 13 relações principais, além de associações N:N |
| 2 N:N com atributo próprio | `associado_cultura` e `safra_cultura` |
| Autorrelacionamento | `associado.id_associado_indicador` |
| Generalização/especialização | `associado` → `associado_pf` / `associado_pj` |
| Entidade fraca | `lote`, identificada por `id_safra + numero_lote` |
| Atributo temporal | `historico_associado.data_inicio/data_fim` |
| 20 regras | RN01 a RN20 documentadas e rastreadas |
| Volume | 40 associados, 40 propriedades, 40 safras, 120 lotes, 160 entregas, 80 prestações e 160 movimentos financeiros |

Os requisitos mínimos do enunciado também incluem o conjunto de 15 consultas e a demonstração de normalização até 3FN.

## Estrutura

```text
.
├── README.md
├── docs/
│   ├── relatorio-etapa1.pdf
│   ├── mer-conceitual.pdf
│   ├── mer-conceitual.drawio
│   ├── modelo-logico.pdf
│   ├── dicionario-dados.pdf
│   ├── A1_escopo_regras.md
│   ├── A3_dicionario_dados.md
│   ├── A4_modelo_logico.md
│   ├── A5_normalizacao.md
│   └── mer_conceitual.dot
└── sql/
    ├── 01_ddl.sql
    ├── 02_carga.sql
    └── 03_consultas.sql
```

## Como executar

### 1. Abrir o MySQL Workbench 8.0

Use uma conexão local com permissão para criar banco de dados.

### 2. Executar o DDL

Abra `sql/01_ddl.sql` e execute o arquivo inteiro.

O script:
- remove o banco anterior `cooperativa_agricola`, se existir;
- cria o banco em `utf8mb4`;
- cria todas as tabelas;
- cria PKs, UNIQUEs, FKs e CHECKs nomeados;
- cria índices auxiliares.

### 3. Executar a carga

Depois de concluir o DDL, execute `sql/02_carga.sql`.

A carga foi produzida com dados sintéticos e inclui casos de contorno, como associados suspensos, histórico com situação pendente, propriedades em regularização, entregas pendentes e prestações em conferência.

### 4. Executar as consultas

Execute `sql/03_consultas.sql`.

As 15 consultas estão divididas em:
- 5 básicas;
- 5 de junções e agregação;
- 5 avançadas.

O conjunto inclui `WHERE`, `ORDER BY`, `LIKE`, `BETWEEN`, `IN`, `NULL`, junção de três ou mais tabelas, `LEFT JOIN`, `GROUP BY`, `HAVING`, subconsulta correlacionada, `EXISTS` e CTE.

## Teste recomendado antes da entrega

1. Remova o banco `cooperativa_agricola`.
2. Execute `01_ddl.sql` do início ao fim.
3. Execute `02_carga.sql` do início ao fim.
4. Execute `03_consultas.sql`.
5. Confirme que não há erros.
6. Verifique as contagens:

```sql
USE cooperativa_agricola;

SELECT 'associado' tabela, COUNT(*) quantidade FROM associado
UNION ALL SELECT 'propriedade', COUNT(*) FROM propriedade
UNION ALL SELECT 'safra', COUNT(*) FROM safra
UNION ALL SELECT 'lote', COUNT(*) FROM lote
UNION ALL SELECT 'historico_associado', COUNT(*) FROM historico_associado
UNION ALL SELECT 'entrega', COUNT(*) FROM entrega
UNION ALL SELECT 'prestacao_contas', COUNT(*) FROM prestacao_contas
UNION ALL SELECT 'movimento_financeiro', COUNT(*) FROM movimento_financeiro;
```

## Rastreabilidade

As regras RN01–RN20 estão documentadas em `docs/A1_escopo_regras.md`. Os principais comandos do DDL possuem comentários indicando as regras implementadas. As regras que dependem de comparação entre tabelas, como a validade temporal da entrega em relação à safra, são verificadas por consulta.

## Documentos

- `docs/relatorio-etapa1.pdf`: relatório consolidado A1–A5.
- `docs/mer-conceitual.pdf`: MER conceitual.
- `docs/mer-conceitual.drawio`: arquivo-fonte editável do diagrama.
- `docs/modelo-logico.pdf`: modelo relacional e decisões de mapeamento.
- `docs/dicionario-dados.pdf`: dicionário de dados.
- `sql/01_ddl.sql`: estrutura física.
- `sql/02_carga.sql`: dados sintéticos.
- `sql/03_consultas.sql`: consultas de verificação.

## Declaração de uso de IA

Foram utilizados assistentes de inteligência artificial como apoio à organização da documentação, geração inicial de trechos de SQL, revisão de consistência entre regras e modelo e preparação dos artefatos. A equipe deve revisar, executar e validar todo o conteúdo antes da entrega e é responsável pelas decisões finais do projeto.
